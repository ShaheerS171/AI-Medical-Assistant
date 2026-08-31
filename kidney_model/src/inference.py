"""
inference.py - Kidney Ultrasound Morphometry Predictor

Uses a DeepLabV3+ segmentation model to measure kidney length (longitudinal view)
and width + thickness (transverse view). Scale factors are read from an Excel
spreadsheet using pandas, matching filenames to physical pixel-spacing values.
"""

import os
from typing import Dict, Optional, Tuple

import cv2
import numpy as np
import pandas as pd
import torch
import segmentation_models_pytorch as smp
import albumentations as A
from PIL import Image

DISCLAIMER = (
    "This is an AI research/decision-support output, not a medical "
    "diagnosis. It does not replace professional radiological assessment."
)

IMG_SIZE = 768

_transform = A.Compose([
    A.LongestMaxSize(max_size=IMG_SIZE),
    A.PadIfNeeded(
        min_height=IMG_SIZE,
        min_width=IMG_SIZE,
        border_mode=cv2.BORDER_CONSTANT,
        fill=0,
        fill_mask=0,
    ),
])


class KidneyUltrasoundPredictor:
    """
    Loads a DeepLabV3+ segmentation model and provides one-call morphometric
    analysis of kidney ultrasound images.
    """

    def __init__(
        self,
        weights_path: str = "kidney_model/weights_fixed.pth",
        excel_path: str = "kidney_model/OpenKidneyUltrasoundDataSet_TransducerInfo.xlsx",
        device: Optional[str] = None,
    ):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.excel_path = excel_path

        # Load model
        self.model = smp.DeepLabV3Plus(
            encoder_name="efficientnet-b3",
            encoder_weights=None,   # weights loaded from file — no internet needed
            in_channels=3,
            classes=2,
        )
        ckpt = torch.load(weights_path, map_location=self.device)
        # Support both raw state-dict and checkpoint dict
        state = ckpt.get("model_state_dict", ckpt)
        self.model.load_state_dict(state)
        self.model.to(self.device)
        self.model.eval()

        # Load scale dataframe with pandas
        self._df = pd.read_excel(excel_path)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _preprocess(self, img_bgr: np.ndarray) -> Tuple[np.ndarray, float]:
        """Return augmented image and pixel→cm scale factor."""
        original_h, original_w = img_bgr.shape[:2]
        scale = min(IMG_SIZE / original_h, IMG_SIZE / original_w)
        aug = _transform(image=img_bgr, mask=None)
        return aug["image"], scale

    def _predict_mask(self, img_bgr: np.ndarray) -> np.ndarray:
        """Run model on a 768×768 BGR image; return binary mask."""
        x = (img_bgr.astype(np.float32) / 255.0)
        x = torch.from_numpy(x).permute(2, 0, 1).unsqueeze(0).to(self.device)
        with torch.no_grad():
            pred = self.model(x)
        mask = pred.argmax(dim=1).squeeze(0).cpu().numpy().astype(np.uint8)
        return mask

    def _findlines(self, mask: np.ndarray, n_axes: int = 1):
        """PCA-based axis extraction from the largest contour."""
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        contour = max(contours, key=cv2.contourArea)
        points = contour[:, 0, :]
        center = points.mean(axis=0)
        centered = points - center
        _, _, pca = np.linalg.svd(centered, full_matrices=False)
        lines = []
        for i in range(n_axes):
            proj = centered @ pca[i]
            lines.append([points[proj.argmin()], points[proj.argmax()]])
        return lines

    def _pixels_to_cm(self, line, scale_factor: float, sx: float, sy: float) -> float:
        """Convert pixel-distance of a line to centimetres."""
        dx = (line[0][0] - line[1][0]) * (abs(sx) / scale_factor)
        dy = (line[0][1] - line[1][1]) * (abs(sy) / scale_factor)
        return float(np.sqrt(dx ** 2 + dy ** 2))

    def _get_scale(self, filename: str) -> Tuple[float, float]:
        """Look up pixel-spacing [cm/pixel] for a given filename via pandas."""
        stem = filename.replace("_anon.png", "").replace(".png", "")
        row = self._df[self._df["Filename"] == stem]
        if row.empty or row["Physical Delta X"].iloc[0] == 1:
            sx = float(self._df["Physical Delta X"].median())
            sy = float(self._df["Physical Delta Y"].median())
        else:
            sx = float(row["Physical Delta X"].iloc[0])
            sy = float(row["Physical Delta Y"].iloc[0])
        return sx, sy

    @staticmethod
    def _draw_line(img_bgr: np.ndarray, line) -> np.ndarray:
        out = img_bgr.copy()
        cv2.line(out, tuple(int(v) for v in line[0]),
                 tuple(int(v) for v in line[1]), (0, 0, 255), 2)
        return out

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def predict(
        self,
        longitudinal_img: Image.Image,
        transverse_img: Image.Image,
        long_filename: str = "unknown",
        trans_filename: str = "unknown",
    ) -> Dict:
        """
        Parameters
        ----------
        longitudinal_img : PIL Image  — coronal/longitudinal view (for length)
        transverse_img   : PIL Image  — transverse view (for width + thickness)
        long_filename    : original filename used to look up scale in Excel
        trans_filename   : original filename used to look up scale in Excel

        Returns
        -------
        dict with length_cm, width_cm, thickness_cm,
                   annotated_longitudinal (PIL), annotated_transverse (PIL),
                   disclaimer
        """
        # Convert PIL → BGR numpy
        img1_bgr = cv2.cvtColor(np.array(longitudinal_img), cv2.COLOR_RGB2BGR)
        img2_bgr = cv2.cvtColor(np.array(transverse_img), cv2.COLOR_RGB2BGR)

        # Pre-process
        img1_pp, scale1 = self._preprocess(img1_bgr)
        img2_pp, scale2 = self._preprocess(img2_bgr)

        # Predict masks
        mask1 = self._predict_mask(img1_pp)
        mask2 = self._predict_mask(img2_pp)

        # Extract measurement lines
        lines1 = self._findlines(mask1, n_axes=1)   # 1 axis – length
        lines2 = self._findlines(mask2, n_axes=2)   # 2 axes – width + thickness
        line_length = lines1[0]
        line_width, line_thickness = lines2[0], lines2[1]

        # Scale lookup via pandas
        sx1, sy1 = self._get_scale(long_filename)
        sx2, sy2 = self._get_scale(trans_filename)

        # Pixel → cm
        length_cm = self._pixels_to_cm(line_length, scale1, sx1, sy1)
        width_cm = self._pixels_to_cm(line_width, scale2, sx2, sy2)
        thickness_cm = self._pixels_to_cm(line_thickness, scale2, sx2, sy2)

        # Build annotated images
        annotated1 = self._draw_line(img1_pp, line_length)
        annotated2 = self._draw_line(img2_pp, line_width)
        annotated2 = self._draw_line(annotated2, line_thickness)

        # Convert back to RGB PIL
        ann1_pil = Image.fromarray(cv2.cvtColor(annotated1, cv2.COLOR_BGR2RGB))
        ann2_pil = Image.fromarray(cv2.cvtColor(annotated2, cv2.COLOR_BGR2RGB))

        return {
            "length_cm": round(length_cm, 2),
            "width_cm": round(width_cm, 2),
            "thickness_cm": round(thickness_cm, 2),
            "annotated_longitudinal": ann1_pil,
            "annotated_transverse": ann2_pil,
            "disclaimer": DISCLAIMER,
        }
