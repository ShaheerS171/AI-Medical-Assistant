"""
Model definition + checkpoint loading for the knee OA ordinal grader.
"""

import torch
import torch.nn as nn
from torchvision import models

NUM_ORDINAL_OUTPUTS = 4
NUM_CLASSES = 5


def build_model(num_ordinal_outputs: int = NUM_ORDINAL_OUTPUTS) -> nn.Module:
    weights = models.EfficientNet_B2_Weights.DEFAULT
    backbone = models.efficientnet_b2(weights=weights)

    for name, param in backbone.features.named_parameters():
        block_num = name.split(".")[0]
        if block_num.isdigit() and int(block_num) < 5:
            param.requires_grad = False

    in_features = backbone.classifier[1].in_features
    backbone.classifier[1] = nn.Sequential(
        nn.Dropout(p=0.45),
        nn.Linear(in_features, num_ordinal_outputs),
    )
    return backbone


def load_trained_model(checkpoint_path: str, device: str = "cpu"):
    model = build_model().to(device)
    ckpt = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()
    return model, ckpt


def ordinal_to_grade(logits: torch.Tensor, thresholds: torch.Tensor):
    probabilities = torch.sigmoid(logits)
    predicted_grade = (probabilities > thresholds).sum(dim=1)
    return predicted_grade, probabilities