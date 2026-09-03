"""
Grad-CAM for the knee OA ordinal grader. This will highlight the infected region predicted by the model
"""

from typing import Tuple
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms

IMG_SIZE = 260
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

# code to normalize the image and resize it so it dont effect the gradient and the model can get the image it was trained on 
_eval_transform = transforms.Compose([
    transforms.Grayscale(num_output_channels=3),
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
])

"""Implementing the Grad-CAM algorithm to visualize the regions of the input image that are most influential for the model's prediction. 
This is particularly useful for understanding the decision-making process of deep learning models in medical imaging tasks, such as knee osteoarthritis severity grading.
This learn the gradient or the most important weight giving the most important part of the system that results in prediction"""

class GradCAM:
    def __init__(self, model: torch.nn.Module, target_layer: torch.nn.Module):
        self.model = model
        self.target_layer = target_layer
        self.activations = None
        self.gradients = None

        self.hook_fwd = target_layer.register_forward_hook(self._save_activations)
        self.hook_bwd = target_layer.register_full_backward_hook(self._save_gradients)

    def _save_activations(self, module, input, output):
        self.activations = output.detach()

    def _save_gradients(self, module, grad_input, grad_output):
        self.gradients = grad_output[0].detach()

    def remove_hooks(self):
        self.hook_fwd.remove()
        self.hook_bwd.remove()

    def generate(self, input_tensor: torch.Tensor, predicted_grade: int) -> np.ndarray:
        self.model.zero_grad()
        logits = self.model(input_tensor)

        if predicted_grade == 0:
            target_score = -logits[0, 0]
        else:
            target_score = logits[0, predicted_grade - 1]

        target_score.backward()

        weights = self.gradients.mean(dim=(2, 3), keepdim=True)
        cam = (weights * self.activations).sum(dim=1, keepdim=True)
        cam = F.relu(cam)

        cam = F.interpolate(cam, size=(IMG_SIZE, IMG_SIZE), mode="bilinear", align_corners=False)
        cam = cam.squeeze().cpu().numpy()

        cam_min, cam_max = cam.min(), cam.max()
        if cam_max - cam_min > 1e-8:
            cam = (cam - cam_min) / (cam_max - cam_min)
        else:
            cam = np.zeros_like(cam)

        return cam

import matplotlib.cm as cm

def overlay_heatmap(original_image: Image.Image, heatmap: np.ndarray, alpha: float = 0.5) -> Image.Image:
    base = original_image.convert("RGB").resize((IMG_SIZE, IMG_SIZE))
    base_arr = np.array(base).astype(np.float32)

    # Use JET colormap. cm.jet(heatmap) returns (H, W, 4) in [0, 1]
    color_map = cm.jet(heatmap)[..., :3] * 255.0

    # The blend factor should be proportional to the heatmap activation.
    # We take the square root of heatmap to slightly boost visibility of lower-activation areas
    # and use a higher alpha (0.7) for a stronger color overlay.
    blend_factor = (heatmap[..., np.newaxis] ** 0.5) * 0.7
    
    blended = (1 - blend_factor) * base_arr + blend_factor * color_map
    blended = np.clip(blended, 0, 255).astype(np.uint8)
    return Image.fromarray(blended)


def get_target_layer(model: torch.nn.Module):
    return model.features[-1]


def run_gradcam(model: torch.nn.Module, image: Image.Image, predicted_grade: int, device: str = "cpu") -> Tuple[Image.Image, np.ndarray]:
    tensor = _eval_transform(image).unsqueeze(0).to(device)

    cam_tool = GradCAM(model, get_target_layer(model))
    try:
        heatmap = cam_tool.generate(tensor, predicted_grade)
    finally:
        cam_tool.remove_hooks()

    overlay = overlay_heatmap(image, heatmap)
    return overlay, heatmap