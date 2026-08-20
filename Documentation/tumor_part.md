# Brain Tumor Detection, Classification & Measurement System

## Production System Documentation & API Specification

---

# 1. System Overview

The Brain Tumor Detection and Measurement System is a production-ready medical imaging pipeline designed to analyze brain MRI scans through a combination of deep learning classification, tumor localization, physical area estimation, and explainable AI visualization.

The system performs three major tasks:

1. **Multi-Class Brain MRI Classification**

   * Utilizes an EfficientNet-B3 convolutional neural network.
   * Categorizes MRI scans into one of four classes:

     * Glioma
     * Meningioma
     * Pituitary Tumor
     * Normal

2. **Tumor Localization & Physical Area Measurement**

   * Employs a custom YOLO object detection model (`tumorbestyolo.pt`) to identify tumor regions.
   * Computes tumor area in:

     * Pixels²
     * Millimeters² (mm²)
     * Centimeters² (cm²)

3. **Visual Explainability**

   * Generates Grad-CAM / LayerCAM heatmaps.
   * Highlights image regions contributing most strongly to model predictions.

---

# 2. Directory Structure

```text
Medical-Assistant/
├── app.py                         # Unified FastAPI REST service layer
├── frontend.py                    # Streamlit dashboard interface
├── requirements.txt               # Project dependencies
│
└── tumor_model/
    ├── modelfiles/
    │   ├── MRIb3.pth              # EfficientNet-B3 classifier weights
    │   └── tumorbestyolo.pt       # YOLO detector weights
    │
    └── src/
        ├── __init__.py
        └── inference.py           # Core inference and measurement engine
```

---

# 3. System Architecture

The inference engine is implemented inside:

```text
tumor_model/src/inference.py
```

The primary class responsible for all prediction workflows is:

```python
BrainTumorPredictor
```

This class encapsulates:

* EfficientNet-B3 classification
* YOLO tumor detection
* Grad-CAM explainability
* Spatial calibration
* Measurement conversion

---

# 4. Classification Pipeline

## Model Architecture

### Backbone

```text
EfficientNet-B3
```

### Output Classes

| Index | Class      |
| ----- | ---------- |
| 0     | Glioma     |
| 1     | Meningioma |
| 2     | Normal     |
| 3     | Pituitary  |

### Classification Head Replacement

The pretrained EfficientNet-B3 classifier layer is replaced with:

```python
nn.Linear(in_features, 4)
```

to support four target categories.

### Prediction Process

1. MRI image loaded.
2. Image resized and normalized.
3. Tensor passed through EfficientNet-B3.
4. Logits generated.
5. Softmax applied.
6. Highest probability class selected.

Mathematically:

[
P(y_i)=\frac{e^{z_i}}{\sum_j e^{z_j}}
]

where:

* (z_i) = class logits
* (P(y_i)) = class probability

---

# 5. Tumor Localization Pipeline

## Detection Model

```text
YOLO
```

Model file:

```text
tumorbestyolo.pt
```

### Detection Output

For every detected tumor:

```text
[x_min, y_min, x_max, y_max]
```

Bounding box coordinates represent:

| Variable | Description     |
| -------- | --------------- |
| x_min    | Left boundary   |
| y_min    | Top boundary    |
| x_max    | Right boundary  |
| y_max    | Bottom boundary |

---

# 6. Tumor Area Measurement

## Pixel Area

The detected tumor area is computed as:

[
Area_{pixels}
=============

(x_{max}-x_{min})
\times
(y_{max}-y_{min})
]

---

## Physical Area Conversion

The system accepts a calibration factor:

```text
mm_per_pixel
```

Default value:

```text
0.5 mm/pixel
```

### Area in mm²

[
Area_{mm^2}
===========

Area_{pixels}
\times
(mm_per_pixel)^2
]

---

### Area in cm²

[
Area_{cm^2}
===========

\frac{Area_{mm^2}}{100}
]

---

## Example

Bounding Box:

```text
Width  = 150 pixels
Height = 95 pixels
```

Pixel Area:

[
150 \times 95 = 14250
]

Using:

```text
mm_per_pixel = 0.5
```

Area:

[
14250 \times 0.25
=================

3562.5 \ mm^2
]

[
35.625 \ cm^2
]

---

# 7. Explainability Pipeline (Grad-CAM)

## Purpose

Grad-CAM provides visual explanations for model predictions by identifying image regions that most strongly influence the classification decision.

---

## Target Layer

The heatmap is generated using the final convolutional feature extractor:

```python
cls_model.features[-1][0]
```

---

## Workflow

1. Forward pass through EfficientNet-B3.
2. Obtain target class score.
3. Backpropagate gradients.
4. Capture:

   * Activations
   * Gradients
5. Compute weighted activation maps.
6. Generate heatmap.
7. Overlay heatmap onto MRI image.

---

## Output

Produces an RGB image highlighting important regions responsible for classification.

---

# 8. Detection Visualization

## Purpose

Provides interpretable localization results from the YOLO detector.

---

## Output Features

* Bounding box overlays
* Detection confidence scores
* RGB image rendering

Example:

```text
Glioma
Confidence: 94.2%
```

displayed directly on the MRI scan.

---

# 9. Core Class Specification

## Constructor

### `__init__(yolo_path, cls_path, device)`

### Responsibilities

* Load YOLO detector.
* Load EfficientNet-B3 classifier.
* Replace classifier head.
* Load model checkpoints.
* Move models to device.
* Set evaluation mode.

### Parameters

| Parameter | Type | Description                  |
| --------- | ---- | ---------------------------- |
| yolo_path | str  | YOLO weights path            |
| cls_path  | str  | EfficientNet checkpoint path |
| device    | str  | cpu or cuda                  |

---

## `predict(image, mm_per_pixel=0.5)`

### Responsibilities

* Perform classification.
* Perform detection.
* Compute tumor measurements.
* Return structured prediction output.

### Returns

```python
{
    "predicted_class": str,
    "confidence": float,
    "probabilities": dict,
    "tumor_area_pixels": float,
    "tumor_area_mm2": float,
    "tumor_area_cm2": float,
    "bounding_box": list
}
```

---

## `generate_gradcam(image, cls_tensor, pred_idx)`

### Responsibilities

* Generate LayerCAM / Grad-CAM visual explanation.
* Overlay heatmap on MRI image.

### Returns

```python
PIL.Image
```

---

## `generate_detection_overlay(det_result)`

### Responsibilities

* Draw YOLO detections.
* Render confidence labels.

### Returns

```python
PIL.Image
```

---

# 10. REST API Specification

## Base URL

```text
http://localhost:8000
```

---

## Endpoint Summary

| Endpoint                   | Method | Request Type        | Response Type | Description                     |
| -------------------------- | ------ | ------------------- | ------------- | ------------------------------- |
| `/brain/predict`           | POST   | multipart/form-data | JSON          | Classification and measurements |
| `/brain/explain-cam`       | POST   | multipart/form-data | image/jpeg    | Grad-CAM visualization          |
| `/brain/explain-detection` | POST   | multipart/form-data | image/jpeg    | Detection visualization         |

---

# 11. API Contract

## POST `/brain/predict`

### Request

Content-Type:

```text
multipart/form-data
```

Field:

```text
file
```

Optional Query Parameter:

```text
mm_per_pixel=0.5
```

---

### Response Example

```json
{
  "predicted_class": "glioma",
  "confidence": 0.9421,
  "probabilities": {
    "glioma": 0.9421,
    "meningioma": 0.0312,
    "normal": 0.0015,
    "pituitary": 0.0252
  },
  "tumor_area_pixels": 14250.0,
  "tumor_area_mm2": 3562.5,
  "tumor_area_cm2": 35.63,
  "bounding_box": [120.5, 84.2, 270.5, 179.2]
}
```

---

## POST `/brain/explain-cam`

### Request

```text
multipart/form-data
```

Field:

```text
file
```

### Response

```text
image/jpeg
```

Returns MRI image overlaid with Grad-CAM heatmap.

---

## POST `/brain/explain-detection`

### Request

```text
multipart/form-data
```

Field:

```text
file
```

### Response

```text
image/jpeg
```

Returns MRI image with YOLO localization overlays.

---

# 12. Deployment Requirements

## Software

* Python 3.10+
* FastAPI
* Uvicorn
* PyTorch
* TorchVision
* OpenCV
* Pillow
* NumPy
* Ultralytics
* Grad-CAM
* Streamlit

---

## System Dependencies

Ubuntu/Debian:

```bash
sudo apt install libgl1
```

---

# 13. Installation

## Create Environment

```bash
conda create -n panda_fix python=3.10
conda activate panda_fix
```

---

## Install Dependencies

```bash
pip install \
torch \
torchvision \
fastapi \
uvicorn \
streamlit \
pillow \
opencv-python \
numpy \
ultralytics \
grad-cam \
requests \
pydantic
```

---

# 14. Running the Application

## Start FastAPI Server

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Server URL:

```text
http://localhost:8000
```

Swagger Documentation:

```text
http://localhost:8000/docs
```

---

## Start Streamlit Dashboard

```bash
streamlit run frontend.py
```

Default URL:

```text
http://localhost:8501
```

---

# 15. End-to-End Inference Workflow

```text
MRI Upload
     │
     ▼
Preprocessing
     │
     ▼
EfficientNet-B3 Classification
     │
     ├──► Predicted Class
     │
     └──► Class Probabilities
     │
     ▼
YOLO Detection
     │
     ├──► Bounding Box
     │
     ├──► Pixel Area
     │
     ├──► mm² Area
     │
     └──► cm² Area
     │
     ▼
Grad-CAM Generation
     │
     ▼
Final Response
     │
     ├── Classification Result
     ├── Confidence Scores
     ├── Tumor Measurements
     ├── Detection Overlay
     └── Explainability Heatmap
```
