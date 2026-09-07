"""
Standalone TB chest X-ray inference script.

Loads the exported TorchScript model (tb_model_traced.pt) for fast inference and
exposes predict_image(), a single function a backend endpoint can call directly.

When tb_model_weights.pth is present alongside this script, predict_image() also
produces a real Grad-CAM overlay by lazily loading the eager TBModel architecture
(reproduced below verbatim from the training notebook) and re-running a single
gradient-enabled forward pass. If the weights file is missing, Grad-CAM degrades
gracefully to a null result with an explanatory note.

Usage:
    from predict import predict_image
    result = predict_image("path/to/xray.png", age=45, sex="M")
    # result = {
    #   "label": "Tuberculosis" | "Normal",
    #   "confidence": 0.9421,
    #   "probabilities": {"Normal": 0.0579, "Tuberculosis": 0.9421},
    #   "gradcam_overlay_png_base64": "<base64 PNG string>" | None,
    #   "gradcam_note": "<str>"  # only present when Grad-CAM could not be produced
    # }
"""
import base64
import io
import json
import types
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image

MODEL_DIR = Path(__file__).parent
TRACED_MODEL_PATH = MODEL_DIR / "tb_model_traced.pt"
WEIGHTS_PATH = MODEL_DIR / "tb_model_weights.pth"
CLASSES_PATH = MODEL_DIR / "tb_classes.json"
PREDICTIONS_DIR = MODEL_DIR / "predictions"

IMG_SIZE = 224
BACKBONE_SOURCE = "xrv"          # matches CHOSEN_SOURCE in the training notebook
MEAN_IMAGENET = [0.485, 0.456, 0.406]
STD_IMAGENET = [0.229, 0.224, 0.225]
SEX_TO_IDX = {'M': 0, 'F': 1, 'unknown': 2}
N_META_FEATURES = 1 + len(SEX_TO_IDX)  # age + one-hot sex = 4
DROPOUT = 0.3

with open(CLASSES_PATH) as f:
    CLASSES = json.load(f)  # {"0": "Normal", "1": "Tuberculosis"}

# ── Fast path: traced TorchScript model (no gradients, used for every prediction) ──
_model = torch.jit.load(str(TRACED_MODEL_PATH), map_location="cpu")
_model.eval()


# =============================================================================
# Eager TBModel — reproduced verbatim from the training notebook (Phase 3 / cell 22)
# so that Grad-CAM has gradients to work with. This MUST stay structurally identical
# to what produced tb_model_weights.pth, or load_state_dict() will fail or silently
# load mismatched weights.
# =============================================================================
class TBModel(nn.Module):
    """
    DenseNet121 (torchxrayvision-pretrained) + tabular age/sex fusion head.

    Image (B, 1, H, W) -> xrv DenseNet backbone -> global-pooled img_feat (B, n_img)
    Meta  (B, 4)        -> Linear(16) -> ReLU -> Dropout -> meta_feat (B, 16)
    Fused (B, n_img+16) -> Linear(256) -> BN -> ReLU -> Dropout -> Linear(2) -> logits
    """

    def __init__(self, backbone_source: str = "xrv",
                 n_meta_features: int = N_META_FEATURES, dropout: float = DROPOUT):
        super().__init__()
        self.backbone_source = backbone_source

        if backbone_source == "xrv":
            import torchxrayvision as xrv
            xrv_backbone = xrv.models.DenseNet(weights="densenet121-res224-all")
            n_img = xrv_backbone.classifier.in_features
            xrv_backbone.classifier = nn.Identity()
            xrv_backbone.op_threshs = None
            self.backbone = xrv_backbone
        else:
            raise ValueError(
                f"This deployment script only supports backbone_source='xrv', got {backbone_source!r}"
            )

        self.meta_fc = nn.Sequential(
            nn.Linear(n_meta_features, 16), nn.ReLU(inplace=True), nn.Dropout(0.3),
        )
        self.head = nn.Sequential(
            nn.Linear(n_img + 16, 256), nn.BatchNorm1d(256), nn.ReLU(inplace=True),
            nn.Dropout(dropout), nn.Linear(256, len(CLASSES)),
        )

    def forward(self, img: torch.Tensor, meta: torch.Tensor) -> torch.Tensor:
        img_feat = self.backbone(img)
        if img_feat.dim() > 2:
            img_feat = torch.flatten(img_feat, 1)
        meta_feat = self.meta_fc(meta)
        return self.head(torch.cat([img_feat, meta_feat], dim=1))


class GradCAM:
    """Hook-based Grad-CAM — architecture-agnostic (only needs a target layer that
    outputs spatial feature maps).

    IMPORTANT Grad-CAM fixes over the original notebook code:
      1. Target layer changed from "last Conv2d" to features.norm5 (the final
         BatchNorm2d before global-avg-pool). In DenseNet's dense blocks each
         conv only produces ~32 channels (growth_rate), but the FULL feature
         map at that point is 1024 channels (all dense-layer outputs concatenated).
         Hooking the last Conv2d captures only that narrow 32-channel slice,
         producing noisy/distorted CAMs. features.norm5 sees ALL 1024 channels.
      2. Activations are saved with .detach().clone() to guard against the
         backbone's inplace F.relu(features, inplace=True) corrupting the saved
         tensor (detach() shares storage; clone() copies it).
      3. The backbone's forward is monkey-patched to use inplace=False for
         the functional ReLU, preventing any inplace mutation issues.
    """

    def __init__(self, model: nn.Module, target_layer: nn.Module):
        self.model = model
        self.activations = None
        self.gradients = None
        self._fh = target_layer.register_forward_hook(self._save_activation)
        self._bh = target_layer.register_full_backward_hook(self._save_gradient)

    def _save_activation(self, module, inp, out):
        # .clone() is critical: xrv DenseNet does F.relu(features, inplace=True)
        # right after self.features(x) returns. .detach() alone shares storage,
        # so the inplace ReLU would zero-out negative activations in our saved
        # copy, distorting the CAM.
        self.activations = out.detach().clone()

    def _save_gradient(self, module, grad_in, grad_out):
        self.gradients = grad_out[0].detach().clone()

    def generate(self, img_tensor: torch.Tensor, meta_tensor: torch.Tensor, class_idx: int = 1) -> np.ndarray:
        self.model.zero_grad()
        logits = self.model(img_tensor, meta_tensor)
        logits[:, class_idx].sum().backward()
        weights = self.gradients.mean(dim=(2, 3), keepdim=True)
        cam = F.relu((weights * self.activations).sum(dim=1)).squeeze().cpu().numpy()
        cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)
        return cam

    def remove_hooks(self):
        self._fh.remove()
        self._bh.remove()


def _get_gradcam_target_layer(backbone: nn.Module) -> nn.Module:
    """Return the best Grad-CAM target layer for the given backbone.

    For xrv DenseNet the correct target is `features.norm5` — the final
    BatchNorm2d that sits right after denseblock4 and right before the
    global average pool. Its output is the complete 1024-channel spatial
    feature map (7×7 at 224-input).

    The old approach (last Conv2d) only captured the ~32 channels produced by
    the very last _DenseLayer, which is a tiny slice of the full representation
    and yields noisy, unlocalized Grad-CAM heatmaps.
    """
    # Try the standard xrv / torchvision DenseNet layout first
    if hasattr(backbone, 'features') and hasattr(backbone.features, 'norm5'):
        return backbone.features.norm5

    # Fallback: last BatchNorm2d with a spatial output
    bns = [m for m in backbone.modules() if isinstance(m, nn.BatchNorm2d)]
    if bns:
        return bns[-1]

    # Ultimate fallback: last Conv2d (least ideal, but better than nothing)
    convs = [m for m in backbone.modules() if isinstance(m, nn.Conv2d)]
    if not convs:
        raise ValueError("No Conv2d or BatchNorm2d layer found in backbone for Grad-CAM.")
    return convs[-1]


def _patch_backbone_for_gradcam(backbone: nn.Module) -> None:
    """Monkey-patch the xrv DenseNet forward to disable inplace ReLU.

    The stock xrv DenseNet.forward() does:
        features = self.features(x)
        out = F.relu(features, inplace=True)   # <── this corrupts hooks
        ...

    We replace it with inplace=False so the norm5 output tensor (which our
    Grad-CAM forward hook saved) is never mutated in place. We also disable
    ALL nn.ReLU(inplace=True) modules inside the backbone for safety.
    """
    # 1. Patch all module-level ReLUs
    for m in backbone.modules():
        if isinstance(m, nn.ReLU):
            m.inplace = False

    # 2. Patch the functional F.relu call in the backbone's forward method
    def _safe_forward(self, x):
        features = self.features(x)
        out = F.relu(features, inplace=False)  # ← the critical fix
        out = F.adaptive_avg_pool2d(out, (1, 1))
        out = torch.flatten(out, 1)
        out = self.classifier(out)
        if hasattr(self, 'apply_sigmoid') and self.apply_sigmoid:
            out = torch.sigmoid(out)
        return out

    backbone.forward = types.MethodType(_safe_forward, backbone)


# ── Lazily-initialized eager model + Grad-CAM (only built on first use, and only
# if the weights file actually exists — keeps import-time cost near zero when
# a caller only wants fast TorchScript predictions). ──
_eager_model: Optional[nn.Module] = None
_gradcam: Optional[GradCAM] = None
_gradcam_init_error: Optional[str] = None


def _get_gradcam() -> Optional[GradCAM]:
    """Builds (once) and returns the eager model + GradCAM helper, or None if
    tb_model_weights.pth is missing or loading fails."""
    global _eager_model, _gradcam, _gradcam_init_error

    if _gradcam is not None:
        return _gradcam
    if _gradcam_init_error is not None:
        return None
    if not WEIGHTS_PATH.exists():
        _gradcam_init_error = f"{WEIGHTS_PATH.name} not found next to predict.py."
        return None

    try:
        model = TBModel(backbone_source=BACKBONE_SOURCE)
        state = torch.load(str(WEIGHTS_PATH), map_location="cpu")
        model.load_state_dict(state)
        model.eval()

        # ── Grad-CAM setup ──
        # 1. Patch inplace ops so hooks are not corrupted
        _patch_backbone_for_gradcam(model.backbone)
        # 2. Pick the right target layer (norm5, NOT last Conv2d)
        target_layer = _get_gradcam_target_layer(model.backbone)

        _eager_model = model
        _gradcam = GradCAM(model, target_layer)
        return _gradcam
    except Exception as exc:  # noqa: BLE001 - surfaced via gradcam_note, not raised
        _gradcam_init_error = f"Failed to initialize eager model/Grad-CAM: {exc}"
        return None


def _preprocess_image(img_gray: np.ndarray) -> tuple:
    """CLAHE + resize + normalize, mirroring the training-time pipeline exactly.

    For the "xrv" backbone this uses torchxrayvision's own normalize() convention
    (roughly [-1024, 1024]), NOT a manual [-1, 1] scale. The eager TBModel's
    backbone (xrv.models.DenseNet) was trained on xrv-normalized input; feeding it
    [-1, 1] values produces out-of-distribution activations and distorted Grad-CAM
    heatmaps even when classification confidence looks plausible.
    """
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    img_gray = clahe.apply(img_gray.astype(np.uint8))
    img_gray = cv2.resize(img_gray, (IMG_SIZE, IMG_SIZE), interpolation=cv2.INTER_AREA)

    if BACKBONE_SOURCE == "imagenet":
        img3 = np.stack([img_gray, img_gray, img_gray], axis=-1).astype(np.float32) / 255.0
        img3 = (img3 - np.array(MEAN_IMAGENET, dtype=np.float32)) / np.array(STD_IMAGENET, dtype=np.float32)
        tensor = torch.from_numpy(img3.transpose(2, 0, 1)).float()
    else:
        # ── xrv normalization: maps [0, 255] → roughly [-1024, 1024] ──
        # This is what xrv.models.DenseNet was pre-trained with.
        import torchxrayvision as xrv
        img_norm = xrv.datasets.normalize(img_gray.astype(np.float64), 255)
        tensor = torch.from_numpy(img_norm).float().unsqueeze(0)  # (1, H, W)

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


def _next_prediction_number() -> int:
    """Scan the predictions folder and return the next available number."""
    if not PREDICTIONS_DIR.exists():
        return 1
    existing = list(PREDICTIONS_DIR.glob("prediction_*.png"))
    if not existing:
        return 1
    numbers = []
    for p in existing:
        stem = p.stem  # e.g. "prediction_003"
        parts = stem.split("_")
        if len(parts) >= 2 and parts[-1].isdigit():
            numbers.append(int(parts[-1]))
    return max(numbers, default=0) + 1


def _save_prediction(overlay_b64: str, result: dict) -> str:
    """Save the Grad-CAM overlay PNG and a companion JSON sidecar to the
    predictions folder with auto-incrementing filenames."""
    PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)
    num = _next_prediction_number()
    tag = f"prediction_{num:03d}"

    png_path = PREDICTIONS_DIR / f"{tag}.png"
    json_path = PREDICTIONS_DIR / f"{tag}.json"

    # Save the overlay image
    with open(png_path, "wb") as f:
        f.write(base64.b64decode(overlay_b64))

    # Save a JSON sidecar with the classification result (omit the huge base64 blob)
    sidecar = {k: v for k, v in result.items() if k != "gradcam_overlay_png_base64"}
    sidecar["overlay_file"] = png_path.name
    with open(json_path, "w") as f:
        json.dump(sidecar, f, indent=2)

    return str(png_path)


def predict_image(image_path_or_bytes, age: float = 33.0, sex: str = "unknown",
                   include_gradcam: bool = True) -> dict:
    """Run inference on a single chest X-ray. age/sex are optional metadata inputs the
    model was trained with; sensible defaults are used if the front-end doesn't collect them.

    Prediction always uses the fast TorchScript model. If include_gradcam=True and
    tb_model_weights.pth is available, a second gradient-enabled forward pass through
    the eager model produces a real Grad-CAM overlay for the predicted class.

    Every prediction with a Grad-CAM overlay is automatically saved into the
    'predictions/' folder with incrementing filenames (prediction_001.png, etc.).
    """
    if isinstance(image_path_or_bytes, (str, Path)):
        pil_img = Image.open(image_path_or_bytes).convert("L")
    else:
        pil_img = Image.open(io.BytesIO(image_path_or_bytes)).convert("L")

    img_gray = np.array(pil_img)
    img_tensor, img_preprocessed = _preprocess_image(img_gray)
    meta_tensor = _build_meta_vector(age, sex)

    # ── Classification via fast TorchScript model (no gradients) ──
    with torch.no_grad():
        logits = _model(img_tensor, meta_tensor)
        probs = torch.softmax(logits, dim=1).squeeze(0).numpy()

    pred_idx = int(probs.argmax())
    result = {
        "label": CLASSES[str(pred_idx)],
        "confidence": round(float(probs[pred_idx]), 4),
        "probabilities": {CLASSES[k]: round(float(probs[int(k)]), 4) for k in CLASSES},
    }

    # ── Grad-CAM via eager model (needs gradients) ──
    if include_gradcam:
        gradcam = _get_gradcam()
        if gradcam is None:
            result["gradcam_overlay_png_base64"] = None
            result["gradcam_note"] = (
                _gradcam_init_error
                or "Grad-CAM unavailable: tb_model_weights.pth not found next to predict.py."
            )
        else:
            try:
                # Clone the tensor and enable gradients for the backward pass.
                # The tensor uses the same xrv-normalized [-1024, 1024] scale
                # that the eager backbone was trained with.
                img_grad = img_tensor.clone().requires_grad_(True)
                cam = gradcam.generate(img_grad, meta_tensor, class_idx=pred_idx)
                b64 = _gradcam_overlay_base64(img_preprocessed, cam)
                result["gradcam_overlay_png_base64"] = b64

                # Auto-save every prediction to the predictions/ folder
                saved_path = _save_prediction(b64, result)
                result["saved_to"] = saved_path
            except Exception as exc:  # noqa: BLE001 - degrade gracefully, never crash predict_image
                result["gradcam_overlay_png_base64"] = None
                result["gradcam_note"] = f"Grad-CAM generation failed: {exc}"

    return result


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python predict.py <path_to_xray_image> [--save-gradcam out.png]")
        sys.exit(1)

    image_path = sys.argv[1]
    save_path = None
    if "--save-gradcam" in sys.argv:
        idx = sys.argv.index("--save-gradcam")
        save_path = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else "gradcam_overlay.png"

    result = predict_image(image_path)

    # The prediction is already auto-saved to predictions/ folder.
    # If --save-gradcam is passed, also save to the explicitly requested path.
    b64 = result.get("gradcam_overlay_png_base64")
    if b64 and save_path:
        with open(save_path, "wb") as f:
            f.write(base64.b64decode(b64))
        print(f"Grad-CAM overlay also saved to: {save_path}")

    # Print result without the huge base64 blob
    display = {k: v for k, v in result.items() if k != "gradcam_overlay_png_base64"}
    if b64:
        display["gradcam_overlay_png_base64"] = f"<{len(b64)} base64 chars, see saved files>"
    print(json.dumps(display, indent=2))

    if result.get("saved_to"):
        print(f"\nPrediction auto-saved to: {result['saved_to']}")
