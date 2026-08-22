# Explainability Engine: Technical Documentation

## Overview

The **Explainability Engine** serves as the interpretability and clinical reasoning layer of the AI Medical Assistant platform. Its primary responsibility is to transform raw machine learning outputs—including classification probabilities, severity grades, Grad-CAM visual explanations, and tumor localization measurements—into structured, clinician-readable assessment reports.

Rather than exposing low-level model predictions directly to end users, the module combines computer vision outputs with Large Language Model (LLM) reasoning to generate professional medical drafts that improve transparency, usability, and decision support.

The explainability layer is designed to support both:

* **Knee Osteoarthritis Assessment**
* **Brain Tumor Classification & Measurement**

while maintaining a unified interface for future medical imaging modules.

---

# Module Architecture

```text
Medical-Assistant/
└── explainability/
    ├── __init__.py
    └── grok_engine.py
```

## Component Responsibilities

### `__init__.py`

Responsible for package initialization and module exposure.

### `grok_engine.py`

Contains the core explainability engine and LLM integration layer.

Primary responsibilities include:

* Interfacing with Mistral AI models
* Translating model predictions into medical language
* Generating structured clinical summaries
* Integrating spatial measurement information
* Incorporating Grad-CAM contextual reasoning
* Producing patient-friendly and clinician-friendly drafts

---

# System Design Philosophy

The Explainability Engine does **not** perform diagnosis.

Its purpose is to:

1. Interpret AI model outputs.
2. Provide contextual medical explanations.
3. Describe likely clinical implications.
4. Suggest commonly recommended follow-up pathways.

The generated reports are intended as **decision-support documentation** and should always be reviewed by qualified healthcare professionals.

---

# Technical Specifications

| Parameter               | Specification             |
| ----------------------- | ------------------------- |
| LLM Provider            | Mistral AI                |
| SDK Dependency          | `mistralai`               |
| Default Model           | `mistral-large-latest`    |
| Sampling Temperature    | `0.3`                     |
| Environment Variable    | `MISTRAL_API_KEY`         |
| Optional Model Override | `MISTRAL_MODEL`           |
| Output Format           | Markdown                  |
| Response Type           | Structured Clinical Draft |

---

# Class Reference

## `MedicalExplainerAPI`

Location:

```python
explainability/grok_engine.py
```

### Constructor

```python
class MedicalExplainerAPI:
    def __init__(
        self,
        api_key: str = None,
        model_name: str = None
    ):
        ...
```

### Responsibilities

Upon initialization the class:

1. Loads environment variables.
2. Initializes the Mistral AI client.
3. Selects the configured LLM model.
4. Prepares reusable prompt templates.
5. Configures deterministic medical report generation parameters.

### Parameters

| Parameter   | Type  | Description                       |
| ----------- | ----- | --------------------------------- |
| api_key     | str   | Optional Mistral API key override |
| model_name  | str   | Optional model override           |
| temperature | float | Fixed internally at 0.3           |

---

# Knee Osteoarthritis Explainability

## Method

```python
generate_knee_report(
    predicted_grade: int,
    confidence: float
)
```

### Purpose

Generates a structured orthopedic assessment based on the predicted Kellgren-Lawrence (KL) grade and model confidence.

---

## Input Parameters

### `predicted_grade`

Type:

```python
int
```

Valid Range:

```text
0 – 4
```

Represents:

| Grade | Interpretation    |
| ----- | ----------------- |
| 0     | No Osteoarthritis |
| 1     | Doubtful OA       |
| 2     | Mild OA           |
| 3     | Moderate OA       |
| 4     | Severe OA         |

---

### `confidence`

Type:

```python
float
```

Represents the classifier confidence score generated from the model softmax output.

Example:

```python
0.912
```

indicates approximately:

```text
91.2% confidence
```

---

## Generated Report Structure

The generated report contains four standardized sections.

### 1. Pathological Interpretation

Describes:

* Joint-space narrowing
* Cartilage degradation
* Osteophyte formation
* Bone sclerosis
* Structural degeneration

---

### 2. Functional Implications

Describes expected patient impacts such as:

* Joint stiffness
* Reduced mobility
* Activity limitations
* Pain progression

---

### 3. Precautionary & Lifestyle Management

May discuss:

* Weight management
* Joint-protection strategies
* Low-impact exercise
* Physical therapy considerations

---

### 4. Recommended Clinical Next Steps

May recommend:

* Orthopedic consultation
* Follow-up imaging
* Conservative treatment
* Surgical evaluation for advanced grades

---

# Brain Tumor Explainability

## Method

```python
generate_tumor_report(
    predicted_class: str,
    confidence: float,
    area_mm2: float,
    area_cm2: float
)
```

### Purpose

Generates a structured neuro-radiological report using:

* Tumor classification
* Classification confidence
* YOLO localization measurements
* Estimated tumor area

---

# Input Parameters

## `predicted_class`

Type:

```python
str
```

Supported Values:

```text
glioma
meningioma
pituitary
no_tumor
```

---

## `confidence`

Type:

```python
float
```

Represents model confidence generated from classification probabilities.

Example:

```python
0.958
```

corresponds to:

```text
95.8% confidence
```

---

## `area_mm2`

Type:

```python
float
```

Represents the localized tumor region area measured in:

[
mm^2
]

Generated from YOLO bounding-box calculations and spatial calibration.

---

## `area_cm2`

Type:

```python
float
```

Represents tumor area converted into:

[
cm^2
]

using:

[
Area_{cm^2}
===========

\frac{Area_{mm^2}}{100}
]

---

# Generated Report Structure

The generated tumor report contains four standardized sections.

---

## 1. Condition Overview & Severity Assessment

Describes:

* Predicted lesion type
* Basic pathological characteristics
* Relative lesion size
* Confidence interpretation

Examples:

* Glioma
* Meningioma
* Pituitary Adenoma
* No Detectable Tumor

---

## 2. Clinical Implications & Risks

Discusses potential considerations such as:

* Neurological symptoms
* Local tissue compression
* Intracranial pressure effects
* Cognitive impacts
* Hormonal disturbances

depending on lesion category.

---

## 3. Precautionary Measures

May include guidance regarding:

* Symptom monitoring
* Medical supervision
* Activity precautions
* Follow-up scheduling

---

## 4. Recommended Diagnostic Follow-Ups

May recommend:

* Contrast-enhanced MRI
* Specialist radiology review
* Neurosurgical consultation
* Endocrinology evaluation
* Tissue biopsy (when clinically appropriate)

---

# Grad-CAM Integration

## Purpose

Grad-CAM visualizations provide spatial explainability for classification decisions.

The Explainability Engine can incorporate metadata derived from Grad-CAM outputs to contextualize:

* Regions of interest
* Model attention patterns
* Anatomical relevance

This improves transparency when presenting AI-generated findings.

---

# Integration Workflow

```text
MRI / X-Ray Input
        │
        ▼
Deep Learning Model
        │
        ├── Classification Scores
        │
        ├── Grad-CAM Heatmap
        │
        └── YOLO Measurements
        │
        ▼
Explainability Engine
        │
        ▼
Mistral AI
        │
        ▼
Structured Clinical Draft
        │
        ▼
FastAPI Response
        │
        ▼
Frontend Visualization
```

---

# Environment Configuration

Create a `.env` file in the project root.

```env
MISTRAL_API_KEY="your_actual_mistral_api_key_here"
MISTRAL_MODEL="mistral-large-latest"
```

---

# Dependency Installation

Install required packages:

```bash
pip install mistralai python-dotenv
```

---

# Usage Example

```python
from explainability.grok_engine import MedicalExplainerAPI

# Initialize client
explainer = MedicalExplainerAPI()

# Generate Knee Osteoarthritis Assessment
knee_draft = explainer.generate_knee_report(
    predicted_grade=3,
    confidence=0.912
)

# Generate Brain Tumor Assessment
brain_draft = explainer.generate_tumor_report(
    predicted_class="glioma",
    confidence=0.958,
    area_mm2=340.5,
    area_cm2=3.41
)

print(knee_draft)
print(brain_draft)
```

---

# Future Enhancements

Planned improvements include:

* Multi-language report generation
* Structured PDF export
* DICOM metadata integration
* Retrieval-Augmented Medical References (RAG)
* Comparative longitudinal patient reports
* Multi-modal image-text explainability
* Specialist-specific reporting templates
* Human-in-the-loop clinical review workflows

---

# Summary

The Explainability Engine provides a robust bridge between deep learning outputs and clinically meaningful narrative reports. By combining computer vision predictions, spatial measurements, Grad-CAM explainability, and Mistral AI reasoning, the module transforms technical model outputs into structured medical documentation suitable for clinician review and decision support workflows.
