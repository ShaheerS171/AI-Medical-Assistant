# Knee Osteoarthritis Severity Grading System
## Production System Documentation & API Specification

---

# 1. System Overview

The **Knee Osteoarthritis Severity Grading System** is an end-to-end computer vision and web application designed to assist in evaluating knee radiograph severity according to the **Kellgren-Lawrence (KL) grading scale (Grades 0–4)**.

Rather than treating diagnostic grading as independent nominal classes, the backend utilizes an **ordinal classification model** built on an **EfficientNet-B2** backbone. The architecture models disease severity as a continuous progression using four ordinal probability thresholds.

The platform includes:

- EfficientNet-B2 based ordinal classifier
- Probability calibration layer
- Grad-CAM explainability engine
- FastAPI inference service
- Streamlit interactive frontend
- Production-ready deployment architecture

> **Disclaimer:** This system is intended for research and decision-support purposes only. It does not replace professional medical diagnosis or radiological assessment.

---

# 2. Directory Structure

```text
knee_oa_project/
├── app.py                      # FastAPI REST API implementation
├── frontend.py                 # Streamlit UI dashboard
├── run_metadata.json           # Calibrated threshold configuration
├── requirements.txt            # System dependencies
├── models/
│   └── knee_ordinal_best.pth   # Pre-trained EfficientNet-B2 weights
└── src/
    ├── __init__.py             # Package initializer
    ├── model.py                # Network architecture & ordinal decoders
    ├── inference.py            # In-memory inference engine & calibrator
    └── gradcam.py              # Visual explainability & heatmap overlays
```

---

# 3. Core Component Architecture

## `src/model.py`

Defines the neural network architecture, loads trained checkpoints, and handles ordinal-to-grade conversion.

### `build_model()`

Initializes an EfficientNet-B2 backbone using ImageNet pre-trained weights.

Key characteristics:

- EfficientNet-B2 feature extractor
- Early layers frozen (`blocks 0–4`)
- Custom classification head
- Ordinal output layer with 4 neurons

Classifier Head:

```python
Dropout(p=0.45)
Linear(in_features, 4)
```

### `load_trained_model()`

Responsibilities:

- Instantiate network architecture
- Load `.pth` checkpoint weights
- Move model to target device (`cpu` or `cuda`)
- Switch model to evaluation mode

```python
model.eval()
```

### `ordinal_to_grade()`

Converts ordinal logits into discrete KL grades.

Process:

1. Apply sigmoid activation
2. Compare probabilities against calibrated thresholds
3. Count passed thresholds
4. Return final grade (0–4)

```text
Thresholds passed → Grade

0 passed = Grade 0
1 passed = Grade 1
2 passed = Grade 2
3 passed = Grade 3
4 passed = Grade 4
```

---

## `src/inference.py`

Provides in-memory image inference functionality.

### `KneeOAPredictor`

Main prediction engine responsible for:

- Image preprocessing
- Model execution
- Threshold calibration
- Probability conversion
- JSON response generation

### `_grade_distribution()`

Converts cumulative ordinal probabilities into discrete grade probabilities.

Output:

```text
P(Grade=0)
P(Grade=1)
P(Grade=2)
P(Grade=3)
P(Grade=4)
```

### `predict()`

Inference workflow:

1. Accept PIL image
2. Apply normalization transforms
3. Execute forward pass
4. Apply threshold calibration
5. Generate probability distribution
6. Return structured prediction response

Inference executes under:

```python
@torch.no_grad()
```

to minimize memory consumption and improve performance.

---

## `src/gradcam.py`

Provides model explainability using Gradient-weighted Class Activation Mapping (Grad-CAM).

### `GradCAM`

Registers hooks on:

```python
model.features[-1]
```

to capture:

- Forward activations
- Backward gradients

Used to generate localized visual explanations showing image regions influencing the prediction.

### Memory Safety

Explicit hook cleanup is implemented:

```python
remove_hooks()
```

This prevents:

- GPU memory leaks
- CPU memory leaks
- Accumulating hook registrations
- Long-running API degradation

### `overlay_heatmap()`

Responsibilities:

1. Generate activation map
2. Convert activation map into RGB heatmap
3. Resize heatmap to image dimensions
4. Blend with original radiograph

Configuration:

```text
Heatmap opacity = 40%
```

Output:

```text
Original X-Ray + Grad-CAM Overlay
```

---

# 4. REST API Specification (`app.py`)

The FastAPI backend exposes a lightweight REST API for model inference and explainability.

The application uses synchronous route handlers, allowing worker thread pools to execute PyTorch operations without blocking the event loop.

---

## Endpoints Summary

| Endpoint | Method | Request Content-Type | Response Content-Type | Description |
|-----------|----------|----------------------|----------------------|-------------|
| `/health` | GET | N/A | application/json | Verify service health and device state |
| `/predict` | POST | multipart/form-data | application/json | Predict KL grade and probabilities |
| `/explain` | POST | multipart/form-data | image/jpeg | Generate Grad-CAM explanation image |

---

# 5. API Payload Contracts

## GET `/health`

### Response

**200 OK**

```json
{
  "status": "healthy",
  "device": "cuda",
  "calibrated": true
}
```

### Field Definitions

| Field | Type | Description |
|---------|--------|-------------|
| status | string | Service health status |
| device | string | Active inference device |
| calibrated | boolean | Whether threshold calibration is enabled |

---

## POST `/predict`

### Request

**Content-Type**

```text
multipart/form-data
```

### Form Fields

| Name | Type | Required |
|--------|--------|-----------|
| file | Binary Image | Yes |

---

### Response

**200 OK**

```json
{
  "predicted_grade": 2,
  "confidence": 0.7842,
  "grade_probabilities": [
    0.021,
    0.113,
    0.784,
    0.071,
    0.011
  ],
  "threshold_probabilities": [
    0.978,
    0.865,
    0.082,
    0.011
  ],
  "calibrated": true,
  "disclaimer": "This is an AI research/decision-support output, not a medical diagnosis. It does not replace professional radiological assessment."
}
```

### Response Fields

| Field | Type | Description |
|---------|--------|-------------|
| predicted_grade | integer | KL grade prediction (0–4) |
| confidence | float | Confidence score for predicted grade |
| grade_probabilities | array | Probability distribution across grades |
| threshold_probabilities | array | Ordinal threshold probabilities |
| calibrated | boolean | Calibration enabled status |
| disclaimer | string | Medical disclaimer |

---

## POST `/explain`

### Request

**Content-Type**

```text
multipart/form-data
```

### Form Fields

| Name | Type | Required |
|--------|--------|-----------|
| file | Binary Image | Yes |

---

### Response

**200 OK**

```text
Content-Type: image/jpeg
```

Returns a JPEG image containing:

```text
Original Radiograph
+
Grad-CAM Activation Overlay
```

Image dimensions:

```text
260 × 260 pixels
```

---

# 6. Local Setup & Running

## Prerequisites

### Software

- Python 3.10+
- pip

### System Dependencies

Ubuntu/Debian:

```bash
sudo apt install libgl1
```

Required for:

- OpenCV
- PIL image processing
- Visualization rendering

---

## Installation

### Clone Repository

```bash
git clone <repository-url>
cd knee_oa_project
```

### Create Virtual Environment

```bash
python -m venv .venv
```

### Activate Environment

Linux / macOS:

```bash
source .venv/bin/activate
```

Windows:

```powershell
.venv\Scripts\activate
```

---

### Install Dependencies

```bash
pip install torch torchvision fastapi uvicorn streamlit plotly pillow requests
```

Or:

```bash
pip install -r requirements.txt
```

---

# 7. Running the Application

## Start FastAPI Backend

```bash
uvicorn app:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4
```

Backend URL:

```text
http://localhost:8000
```

Interactive API Documentation:

```text
http://localhost:8000/docs
```

Alternative OpenAPI Schema:

```text
http://localhost:8000/redoc
```

---

## Start Streamlit Frontend

```bash
streamlit run frontend.py
```

Frontend URL:

```text
http://localhost:8501
```

---

# 8. Deployment Notes

### Recommended Production Configuration

#### Backend

- FastAPI
- Uvicorn Workers
- Nginx Reverse Proxy

#### Model Serving

- GPU Inference (CUDA)
- Mixed Precision Inference
- Batch Size = 1 (real-time prediction)

#### Monitoring

- Health endpoint checks
- GPU memory monitoring
- Request latency tracking
- Exception logging

---

# 9. Safety Notice

This software is intended solely for:

- Academic research
- Computer vision experimentation
- Clinical decision support

This system:

- Does **not** diagnose disease
- Does **not** replace a radiologist
- Does **not** provide medical advice

All outputs should be reviewed by qualified healthcare professionals before any clinical use.

---

# Version Information

| Component | Version |
|------------|------------|
| Model Backbone | EfficientNet-B2 |
| Classification Type | Ordinal Classification |
| Explainability | Grad-CAM |
| Backend | FastAPI |
| Frontend | Streamlit |
| API Standard | REST |
| Supported Grades | KL 0–4 |

---