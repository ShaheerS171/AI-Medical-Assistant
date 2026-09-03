<div align="center">

# AI Medical Assistant

### Multi-Modal Clinical Decision Support Platform

**An AI-powered healthcare system that combines medical imaging, retrieval-augmented generation, and explainable diagnostics to assist clinicians with evidence-backed decision making.**

<p>

[Live Demo Badge]
[FastAPI Badge]
[React Badge]
[PyTorch Badge]
[Mistral Badge]
[Supabase Badge]

</p>

</div>

---

## The Problem

Medical AI models are becoming increasingly accurate, but most remain black boxes.

Clinicians are often presented with a prediction without understanding:

- Why the prediction was made
- What evidence supports it
- How confident the model is
- Whether the recommendation can be trusted

Meanwhile, healthcare chatbots frequently hallucinate information, creating significant risks in clinical settings.

The healthcare industry needs AI systems that are not only accurate, but also transparent, explainable, and evidence-driven.

---

## The Solution

AI Medical Assistant combines:

- Computer Vision
- Retrieval-Augmented Generation
- Explainable AI
- Clinical Decision Support

into a unified platform.

Instead of providing only a diagnosis, the system:

1. Analyzes medical scans
2. Generates confidence-aware predictions
3. Explains the findings
4. Retrieves supporting medical literature
5. Produces evidence-backed clinical reasoning
6. Recommends appropriate specialists

Every prediction is paired with contextual information designed to increase clinician trust and reduce AI hallucinations.

---

## Demo

[screenshot]

Live Demo: https://...

Video Demo: https://...

---

## Features

### Brain MRI Analysis

Detects and classifies brain tumors from MRI scans.

Capabilities:

- Multi-class classification
- Confidence scoring
- Explainable outputs
- Clinical interpretation

---

### Knee Osteoarthritis Assessment

Automated Kellgren-Lawrence grading.

Capabilities:

- Severity classification
- Confidence distribution
- Clinical recommendations

---

### Kidney Ultrasound Morphometry

Automated kidney structure assessment.

Capabilities:

- Morphometric measurements
- Anomaly detection
- Structured reporting

---

### Grounded Medical Consultation

Unlike traditional healthcare chatbots, responses are generated using retrieved medical evidence.

Sources include:

- PubMed
- WHO Guidelines
- Clinical Literature

This significantly reduces hallucination risk.

---

### Specialist Recommendation Engine

Maps findings to relevant healthcare specialties:

- Neurology
- Neurosurgery
- Orthopedics
- Nephrology

---

## Architecture

[large architecture diagram]

React Frontend
↓
FastAPI Backend
↓
Vision Models
↓
RAG Engine
↓
ChromaDB
↓
Medical Literature

---

## AI Systems

### Brain MRI Model

Purpose:
Brain tumor classification

Architecture:
EfficientNet-B3

Outputs:

- Class prediction
- Confidence score
- Explainability data

---

### Knee Osteoarthritis Model

Purpose:
KL grading

Architecture:
EfficientNet-B2 Ordinal Classification

Outputs:

- Grade 0–4
- Confidence distribution

---

### Kidney Ultrasound Engine

Purpose:
Morphometric analysis

Outputs:

- Measurements
- Abnormality indicators

---

### Medical RAG Agent

Purpose:
Evidence-grounded consultation

Pipeline:

Query
↓
Embedding Search
↓
ChromaDB Retrieval
↓
Context Augmentation
↓
Mistral AI
↓
Citation-backed Response

---

## Technology Stack

| Layer | Technology |
|---------|---------|
| Frontend | React, Vite, Framer Motion |
| Backend | FastAPI |
| Vision AI | PyTorch |
| RAG | LangChain, ChromaDB |
| LLM | Mistral AI |
| Auth | Supabase |
| Deployment | Docker |

---

## Future Roadmap

- Grad-CAM Explainability
- DICOM Support
- Clinical PDF Reports
- Longitudinal Patient Tracking
- Additional Imaging Modalities
- Doctor Dashboard

---

## Why This Matters

AI Medical Assistant is not designed to replace physicians.

It is designed to help healthcare professionals make faster, more informed, and evidence-backed decisions by combining modern AI with transparent clinical reasoning.

---

## Contributors

Your names

---

## License

MIT License
