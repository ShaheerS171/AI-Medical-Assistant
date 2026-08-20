"""
Single-image inference for the knee OA ordinal grader.
"""

import json
import os
from typing import Dict

import torch
from PIL import Image
from torchvision import transforms

from knee_model.src.model import load_trained_model, ordinal_to_grade

IMG_SIZE = 260
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

DISCLAIMER = (
    "This is an AI research/decision-support output, not a medical "
    "diagnosis. It does not replace professional radiological assessment."
)

_eval_transform = transforms.Compose([
    transforms.Grayscale(num_output_channels=3),
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
])

"""This class contains the code for the knee predictor. It will take the image preprocess it to make it equal to the
system and then it will use the model to predict the grade of the knee ostreoarthiritis and gives back the proper JSON 
structure as a return"""

class KneeOAPredictor:
    def __init__(
        self,
        checkpoint_path: str = "models/knee_ordinal_best.pth",
        metadata_path: str = "run_metadata.json",
        device: str = None,
    ):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model, self.ckpt = load_trained_model(checkpoint_path, device=self.device)

        if os.path.exists(metadata_path):
            with open(metadata_path) as f:
                meta = json.load(f)
            self.thresholds = torch.tensor(meta["calibrated_thresholds"], dtype=torch.float32)
            self.calibrated = True
        else:
            self.thresholds = torch.full((4,), 0.5)
            self.calibrated = False

        self.thresholds = self.thresholds.to(self.device)

    @staticmethod
    def _grade_distribution(probs: torch.Tensor) -> torch.Tensor:
        p_gt = probs
        p_grade = torch.zeros(5)
        p_grade[0] = 1 - p_gt[0]
        p_grade[1] = p_gt[0] - p_gt[1]
        p_grade[2] = p_gt[1] - p_gt[2]
        p_grade[3] = p_gt[2] - p_gt[3]
        p_grade[4] = p_gt[3]
        p_grade = torch.clamp(p_grade, min=0.0)
        total = p_grade.sum()
        if total > 0:
            p_grade = p_grade / total
        return p_grade

    @torch.no_grad()
    def predict(self, image: Image.Image) -> Dict:
        tensor = _eval_transform(image).unsqueeze(0).to(self.device)

        logits = self.model(tensor)
        predicted_grade, probs = ordinal_to_grade(logits, self.thresholds)

        probs = probs.squeeze(0).cpu()
        grade_dist = self._grade_distribution(probs)
        predicted_grade = int(predicted_grade.item())
        confidence = float(grade_dist[predicted_grade].item())

        return {
            "predicted_grade": predicted_grade,
            "confidence": confidence,
            "grade_probabilities": grade_dist.tolist(),
            "threshold_probabilities": probs.tolist(),
            "calibrated": self.calibrated,
            "disclaimer": DISCLAIMER,
        }