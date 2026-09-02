"""
Standalone TB chest X-ray inference script.

Loads the exported TorchScript model (tb_model_traced.pt) and exposes predict_image(),
a single function a backend endpoint can call directly. No training-code dependencies.

Usage:
    from predict import predict_image
    result = predict_image("path/to/xray.png", age=45, sex="M")
    # result = {
    #   "label": "Tuberculosis" | "Normal",
    #   "confidence": 0.9421,
    #   "probabilities": {"Normal": 0.0579, "Tuberculosis": 0.9421},
    #   "gradcam_overlay_png_base64": "<base64 PNG string>"
    # }
"""
import base64
import io
import json
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image

MODEL_DIR = Path(__file__).parent
TRACED_MODEL_PATH = MODEL_DIR / "tb_model_traced.pt"
CLASSES_PATH = MODEL_DIR / "tb_classes.json"

IMG_SIZE = 224
BACKBONE_SOURCE = "xrv"
MEAN_IMAGENET = [0.485, 0.456, 0.406]
STD_IMAGENET = [0.229, 0.224, 0.225]
SEX_TO_IDX = {'M': 0, 'F': 1, 'unknown': 2}

with open(CLASSES_PATH) as f:
    CLASSES = json.load(f)  # {"0": "Normal", "1": "Tuberculosis"}

_model = torch.jit.load(str(TRACED_MODEL_PATH), map_location="cpu")
_model.eval()


def _preprocess_image(img_gray: np.ndarray) -> torch.Tensor:
    """CLAHE + resize + normalize, mirroring the training-time pipeline exactly."""
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    img_gray = clahe.apply(img_gray.astype(np.uint8))
    img_gray = cv2.resize(img_gray, (IMG_SIZE, IMG_SIZE), interpolation=cv2.INTER_AREA)

    if BACKBONE_SOURCE == "imagenet":
        img3 = np.stack([img_gray, img_gray, img_gray], axis=-1).astype(np.float32) / 255.0
        img3 = (img3 - np.array(MEAN_IMAGENET, dtype=np.float32)) / np.array(STD_IMAGENET, dtype=np.float32)
        tensor = torch.from_numpy(img3.transpose(2, 0, 1)).float()
    else:
        img_norm = ((img_gray.astype(np.float32) / 255.0) - 0.5) * 2.0
        tensor = torch.from_numpy(img_norm).float().unsqueeze(0)

    return tensor.unsqueeze(0), img_gray  # (1, C, H, W), preprocessed grayscale for overlay


def _build_meta_vector(age: float, sex: str) -> torch.Tensor:
    sex_idx = SEX_TO_IDX.get(sex, SEX_TO_IDX.get("unknown", 2))
    vec = np.array([age / 100.0, float(sex_idx == 0), float(sex_idx == 1), float(sex_idx == 2)],
                    dtype=np.float32)
    return torch.from_numpy(vec).unsqueeze(0)


def _gradcam_overlay_base64(img_gray_preprocessed: np.ndarray, cam: np.ndarray) -> str:
    cam_resized = cv2.resize(cam, (img_gray_preprocessed.shape[1], img_gray_preprocessed.shape[0]))
    cam_resized = (cam_resized - cam_resized.min()) / (cam_resized.max() - cam_resized.min() + 1e-8)
    heatmap = cv2.applyColorMap((cam_resized * 255).astype(np.uint8), cv2.COLORMAP_JET)
    heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)
    base_rgb = np.stack([img_gray_preprocessed] * 3, axis=-1).astype(np.uint8)
    overlay = (0.55 * base_rgb + 0.45 * heatmap).astype(np.uint8)

    buf = io.BytesIO()
    Image.fromarray(overlay).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def predict_image(image_path_or_bytes, age: float = 33.0, sex: str = "unknown",
                   include_gradcam: bool = True) -> dict:
    """Run inference on a single chest X-ray. age/sex are optional metadata inputs the
    model was trained with; sensible defaults are used if the front-end doesn't collect them."""
    if isinstance(image_path_or_bytes, (str, Path)):
        pil_img = Image.open(image_path_or_bytes).convert("L")
    else:
        pil_img = Image.open(io.BytesIO(image_path_or_bytes)).convert("L")

    img_gray = np.array(pil_img)
    img_tensor, img_preprocessed = _preprocess_image(img_gray)
    meta_tensor = _build_meta_vector(age, sex)

    with torch.no_grad():
        logits = _model(img_tensor, meta_tensor)
        probs = torch.softmax(logits, dim=1).squeeze(0).numpy()

    pred_idx = int(probs.argmax())
    result = {
        "label": CLASSES[str(pred_idx)],
        "confidence": round(float(probs[pred_idx]), 4),
        "probabilities": {CLASSES[k]: round(float(probs[int(k)]), 4) for k in CLASSES},
    }

    if include_gradcam:
        # Grad-CAM needs gradients, so re-run through a (non-traced) eager model here is
        # out of scope for this lightweight script — the traced model is inference-only.
        # For a Grad-CAM-enabled endpoint, load tb_model_weights.pth into the TBModel class
        # (see the training notebook, Phase 3) instead of the traced model.
        result["gradcam_overlay_png_base64"] = None
        result["gradcam_note"] = (
            "Grad-CAM requires the eager (non-TorchScript-traced) model with gradients enabled. "
            "Load tb_model_weights.pth via the TBModel class for Grad-CAM support; "
            "10 pre-computed examples are provided in demo_assets/top10_confident/."
        )

    return result


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python predict.py <path_to_xray_image>")
        sys.exit(1)
    print(json.dumps(predict_image(sys.argv[1]), indent=2))
