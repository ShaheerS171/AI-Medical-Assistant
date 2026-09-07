"""
tb_model/src/inference.py - Predictor wrapper for Tuberculosis Detection
"""

import sys
from pathlib import Path
from typing import Dict, Any, Union
from PIL import Image

# Ensure TB_model 1 directory is accessible in sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_TB_DIR = _PROJECT_ROOT / "TB_model 1"
if str(_TB_DIR) not in sys.path:
    sys.path.insert(0, str(_TB_DIR))

from predict import predict_image


class TBPredictor:
    """
    Wrapper around the DenseNet121 TB Chest X-ray predictor.
    Handles image bytes or file paths, age, and sex metadata inputs,
    and returns class predictions, probabilities, and Grad-CAM overlays.
    """

    def __init__(self):
        # The underlying model is initialized inside TB_model 1/predict.py
        pass

    def predict(
        self,
        image_input: Union[bytes, str, Path],
        age: float = 33.0,
        sex: str = "unknown",
        include_gradcam: bool = True,
    ) -> Dict[str, Any]:
        """
        Runs TB screening inference.
        Returns:
            {
                "label": "Tuberculosis" | "Normal",
                "confidence": float,
                "probabilities": {"Normal": float, "Tuberculosis": float},
                "gradcam_overlay_png_base64": str | None,
                "gradcam_note": str (optional),
                "saved_to": str (optional)
            }
        """
        # Normalize sex string for SEX_TO_IDX in predict.py ('M', 'F', 'unknown')
        sex_str = str(sex).strip().upper()
        if sex_str.startswith("M"):
            norm_sex = "M"
        elif sex_str.startswith("F"):
            norm_sex = "F"
        else:
            norm_sex = "unknown"

        return predict_image(
            image_path_or_bytes=image_input,
            age=float(age),
            sex=norm_sex,
            include_gradcam=include_gradcam,
        )
