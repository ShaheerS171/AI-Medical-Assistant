import torch
import torch.nn as nn
import numpy as np
from PIL import Image
from torchvision.models import efficientnet_b3
from torchvision import transforms
from ultralytics import YOLO
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget
from pytorch_grad_cam.utils.image import show_cam_on_image

CLS_LABELS = ['glioma', 'meningioma', 'normal', 'pituitary']

cls_transform = transforms.Compose([
    transforms.Resize((300, 300)),
    transforms.ToTensor(),
    transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225))
])


class BrainTumorPredictor:
    def __init__(
        self,
        yolo_path: str = "tumor_model/modelfiles/tumorbestyolo.pt",
        cls_path: str = "tumor_model/modelfiles/MRIb3.pth",
        device: str = None
    ):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        
        self.det_model = YOLO(yolo_path)
        
        self.cls_model = efficientnet_b3()
        self.cls_model.classifier[1] = nn.Linear(self.cls_model.classifier[1].in_features, 4)
        
        ckpt = torch.load(cls_path, map_location=self.device)
        if "model_state_dict" in ckpt:
            self.cls_model.load_state_dict(ckpt["model_state_dict"])
        else:
            self.cls_model.load_state_dict(ckpt)
            
        self.cls_model.to(self.device)
        self.cls_model.eval()

    def predict(self, image: Image.Image, mm_per_pixel: float = 0.5) -> dict:
        cls_tensor = cls_transform(image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            logits = self.cls_model(cls_tensor)
            probs = torch.softmax(logits, dim=1).squeeze(0)
            pred_idx = int(logits.argmax(dim=1).item())

        img_np = np.array(image)
        det_res = self.det_model.predict(img_np, conf=0.5, verbose=False)
        
        area_pixels = None
        area_mm2 = None
        area_cm2 = None
        box_coords = []

        if len(det_res[0].boxes) > 0:
            box = det_res[0].boxes.xyxy[0].cpu().numpy()
            width = float(box[2] - box[0])
            height = float(box[3] - box[1])
            
            area_pixels = float(width * height)
            area_mm2 = area_pixels * (mm_per_pixel ** 2)
            area_cm2 = area_mm2 / 100.0
            box_coords = [float(x) for x in box]

        return {
            "predicted_class": CLS_LABELS[pred_idx],
            "confidence": float(probs[pred_idx].item()),
            "probabilities": {label: float(probs[i].item()) for i, label in enumerate(CLS_LABELS)},
            "tumor_area_pixels": area_pixels,
            "tumor_area_mm2": area_mm2,
            "tumor_area_cm2": area_cm2,
            "bounding_box": box_coords,
            "det_result": det_res[0],
            "cls_tensor": cls_tensor,
            "pred_idx": pred_idx
        }

    def generate_gradcam(self, image: Image.Image, cls_tensor: torch.Tensor, pred_idx: int) -> Image.Image:
        target_layers = [self.cls_model.features[-1][0]]
        cam = GradCAM(model=self.cls_model, target_layers=target_layers)
        
        targets = [ClassifierOutputTarget(pred_idx)]
        graycam = cam(input_tensor=cls_tensor, targets=targets)[0]
        
        display_img = cls_transform(image).permute(1, 2, 0).numpy()
        display_img = display_img * np.array([0.229, 0.224, 0.225]) + np.array([0.485, 0.456, 0.406])
        display_img = np.clip(display_img, 0, 1)
        
        visualization = show_cam_on_image(display_img, graycam, use_rgb=True)
        return Image.fromarray(visualization)

    def generate_detection_overlay(self, det_result) -> Image.Image:
        box_img = det_result.plot()
        box_img_rgb = box_img[:, :, ::-1]
        return Image.fromarray(box_img_rgb)