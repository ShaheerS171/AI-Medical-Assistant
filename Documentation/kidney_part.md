# Kidney Ultrasound Morphometry System
## Production System Documentation & API Specification

---

# 1. System Overview

The **Kidney Ultrasound Morphometry System** is an end-to-end computer vision and web application designed to assist in automated measurement of kidney dimensions from B-mode ultrasound images.

The system uses a **DeepLabV3+** segmentation model with an **EfficientNet-B3** encoder to produce pixel-accurate kidney contours. From these contours, **PCA-based axis extraction** computes three clinically relevant morphometric measurements:

- **Length** — from the longitudinal (coronal) view
- **Width** — from the transverse view
- **Thickness** — from the transverse view

Scale conversion from pixels to centimetres is performed using physical pixel-spacing values sourced from the accompanying Excel metadata file via **pandas**.

The platform includes:

- DeepLabV3+ segmentation model (EfficientNet-B3 encoder)
- PCA-based axis extraction for morphometric measurement
- Pandas-based pixel→cm scale correction
- Mistral AI radiology report generation
- FastAPI inference service
- Streamlit interactive frontend
- PDF report export

> **Disclaimer:** This system is intended for research and decision-support purposes only. It does not replace professional medical diagnosis or radiological assessment.

---

# 2. Directory Structure

```text
kidney_model/
├── weights_fixed.pth                              # Pre-trained DeepLabV3+ weights (re-zipped)
├── OpenKidneyUltrasoundDataSet_TransducerInfo.xlsx  # Pixel-spacing metadata (pandas)
├── KidneyReport.py                                # Original research script
├── requirements.txt                               # Module dependencies
├── [sample ultrasound images]
└── src/
    ├── __init__.py        # Package initializer
    └── inference.py       # Segmentation engine & morphometric predictor
```

---

# 3. Core Component Architecture

## `src/inference.py`

Provides the full segmentation and morphometry pipeline.

### `KidneyUltrasoundPredictor`

Main prediction engine responsible for:

- Loading the DeepLabV3+ model
- Image preprocessing (resize + pad to 768×768)
- Segmentation mask inference
- Contour extraction and PCA-based axis fitting
- Scale lookup via pandas
- Pixel-to-centimetre conversion
- Annotated overlay image generation

---

### `_preprocess()`

Applies the Albumentations preprocessing pipeline to a BGR image:

```python
A.LongestMaxSize(max_size=768)
A.PadIfNeeded(min_height=768, min_width=768, border_mode=BORDER_CONSTANT)
```

Returns:
- Preprocessed 768×768 image
- Pixel scale factor (`min(768/h, 768/w)`)

---

### `_predict_mask()`

Runs a single forward pass through DeepLabV3+:

1. Normalize pixel values to `[0, 1]`
2. Convert BGR numpy array to `(C, H, W)` tensor
3. Run model inference under `torch.no_grad()`
4. `argmax` across class dimension → binary mask

---

### `_findlines()`

Extracts principal measurement axes from the largest kidney contour using **Singular Value Decomposition (SVD)**:

Process:
1. Extract largest contour via `cv2.findContours`
2. Centre points around centroid
3. Apply SVD (PCA) to find principal axes
4. Project points onto each axis
5. Return endpoints of measurement lines

```text
Longitudinal view → 1 axis  → Length line
Transverse view   → 2 axes  → Width + Thickness lines
```

---

### `_get_scale()`

Performs pandas-based pixel-spacing lookup:

```python
df = pd.read_excel(excel_path)
row = df[df["Filename"] == stem]
sx = row["Physical Delta X"].iloc[0]   # cm/pixel (X)
sy = row["Physical Delta Y"].iloc[0]   # cm/pixel (Y)
```

Fallback: uses **dataset median** pixel-spacing when the filename is not found or spacing is invalid (`== 1`).

---

### `_pixels_to_cm()`

Converts pixel-space line endpoints to centimetres using the scale factor:

```python
dx = (line[0][0] - line[1][0]) * (abs(sx) / scale_factor)
dy = (line[0][1] - line[1][1]) * (abs(sy) / scale_factor)
length_cm = sqrt(dx² + dy²)
```

---

### `predict()`

Full inference pipeline — accepts two PIL images and returns structured results:

**Inputs:**

| Parameter | Type | Description |
|---|---|---|
| `longitudinal_img` | PIL Image | Coronal/longitudinal view (for length) |
| `transverse_img` | PIL Image | Transverse view (for width & thickness) |
| `long_filename` | str | Original filename for scale lookup |
| `trans_filename` | str | Original filename for scale lookup |

**Outputs:**

```json
{
  "length_cm": 10.42,
  "width_cm": 4.87,
  "thickness_cm": 3.21,
  "annotated_longitudinal": "<PIL Image>",
  "annotated_transverse": "<PIL Image>",
  "disclaimer": "This is an AI research/decision-support output..."
}
```

---

# 4. REST API Specification (`app.py`)

## Endpoints Summary

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Service health check |
| `/predict/kidney-ultrasound` | POST | Segment images & return morphometric measurements |

---

## POST `/predict/kidney-ultrasound`

### Request

**Content-Type:**
```text
multipart/form-data
```

### Form Fields

| Name | Type | Required | Description |
|---|---|---|---|
| `longitudinal` | Binary Image | Yes | Longitudinal (coronal) kidney ultrasound |
| `transverse` | Binary Image | Yes | Transverse kidney ultrasound |

### Response

**200 OK**

```json
{
  "length_cm": 10.42,
  "width_cm": 4.87,
  "thickness_cm": 3.21
}
```

### Response Fields

| Field | Type | Description |
|---|---|---|
| `length_cm` | float | Kidney length measured from longitudinal view |
| `width_cm` | float | Kidney width measured from transverse view |
| `thickness_cm` | float | Kidney thickness measured from transverse view |

### Error Responses

| Code | Reason |
|---|---|
| 400 | Uploaded file is not an image |
| 500 | Segmentation or measurement processing failed |

---

# 5. Mistral AI Report Generation

The `MedicalExplainerAPI.generate_kidney_report()` method generates a formal **5-section clinical radiology report** using the measured morphometrics and patient metadata.

### Prompt Inputs

| Parameter | Description |
|---|---|
| `length_cm` | Kidney length (cm) |
| `width_cm` | Kidney width (cm) |
| `thickness_cm` | Kidney thickness (cm) |
| `patient_info` | Dict with `name`, `id`, `age`, `sex`, `history` |

### Report Sections

1. **Patient & Examination Header** — Demographics, modality, examination context
2. **Clinical History & Indication** — Chief complaints and renal evaluation rationale
3. **Technique & Visual Observations** — B-mode technique, segmentation measurements
4. **Detailed Radiological Findings** — Morphometric interpretation vs. normal ranges
5. **Impression & Clinical Recommendations** — Actionable next steps

### Normal Adult Reference Ranges

| Measurement | Normal Range |
|---|---|
| Length | 9 – 12 cm |
| Width | 4 – 6 cm |
| Thickness | 3 – 5 cm |

---

# 6. Streamlit Frontend (`frontend.py`)

The **🫘 Kidney Ultrasound (Morphometry)** module is accessible from the sidebar navigation.

### User Workflow

1. Upload **longitudinal** ultrasound image (PNG/JPG)
2. Upload **transverse** ultrasound image (PNG/JPG)
3. Fill in patient intake form (name, ID, age, sex, history)
4. Click **Run Segmentation & Generate Report**
5. Review annotated overlays and morphometric metrics
6. Read Mistral-generated clinical report
7. Download PDF report

### Displayed Outputs

| Output | Description |
|---|---|
| Annotated Longitudinal | Image with length measurement line drawn |
| Annotated Transverse | Image with width & thickness lines drawn |
| Kidney Length metric | Measured length in cm |
| Kidney Width metric | Measured width in cm |
| Kidney Thickness metric | Measured thickness in cm |
| Clinical Report | Mistral 5-section radiology draft |
| PDF Download | Full report export |

---

# 7. Local Setup & Running

## Prerequisites

- Python 3.10+
- Conda environment: `panda_fix`

## Install Dependencies

```bash
conda activate panda_fix
pip install segmentation-models-pytorch albumentations opencv-python-headless torch pandas openpyxl streamlit fastapi uvicorn
```

## Run Streamlit Frontend

```bash
conda activate panda_fix
streamlit run frontend.py
```

Frontend URL:
```text
http://localhost:8501
```

## Run FastAPI Backend

```bash
conda activate panda_fix
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Interactive API Docs:
```text
http://localhost:8000/docs
```

---

# 8. Weights File Note

The model weights are stored as `kidney_model/weights_fixed.pth`. The original uploaded `weights.pth` was a directory (unzipped PyTorch ZIP archive). It was re-zipped with correct timestamps to produce a valid PyTorch checkpoint file loadable via `torch.load`.

Checkpoint keys:
```json
["model_state_dict", "loss", "dice_score"]
```

---

# 9. Safety Notice

This software is intended solely for:

- Academic research
- Computer vision experimentation
- Clinical decision support

This system:

- Does **not** diagnose disease
- Does **not** replace a radiologist or nephrologist
- Does **not** provide medical advice

All outputs should be reviewed by qualified healthcare professionals before any clinical use.

---

# Version Information

| Component | Version |
|---|---|
| Model Architecture | DeepLabV3+ |
| Encoder Backbone | EfficientNet-B3 |
| Segmentation Classes | 2 (background, kidney) |
| Input Resolution | 768 × 768 |
| Scale Source | Pandas (Excel metadata) |
| Backend | FastAPI |
| Frontend | Streamlit |
| Report Engine | Mistral AI (`mistral-small-latest`) |
| API Standard | REST |

---
