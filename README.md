<div align="center">

<img src="./assets/logo.png" width="120">

# AI Medical Assistant

### Multi-Modal Clinical Decision Support Platform

**An AI-powered healthcare platform that combines Computer Vision, Retrieval-Augmented Generation, and Explainable AI to deliver evidence-backed clinical insights.**

<p>

<img src="https://img.shields.io/badge/FastAPI-Backend-009688?style=flat-square&logo=fastapi&logoColor=white">
<img src="https://img.shields.io/badge/React-Frontend-61DAFB?style=flat-square&logo=react&logoColor=black">
<img src="https://img.shields.io/badge/PyTorch-Vision_AI-EE4C2C?style=flat-square&logo=pytorch&logoColor=white">
<img src="https://img.shields.io/badge/Mistral-LLM-orange?style=flat-square">
<img src="https://img.shields.io/badge/Supabase-Authentication-3ECF8E?style=flat-square&logo=supabase&logoColor=white">

</p>

<p>

<a href="https://your-demo-link.com">
  <img src="https://img.shields.io/badge/Live-Demo-success?style=for-the-badge">
</a>

<a href="https://youtube.com/watch?v=your-video">
  <img src="https://img.shields.io/badge/Video-Demo-red?style=for-the-badge">
</a>

</p>

</div>

---

## Built For

**[Hackathon Name 2026]**

---

## The Problem

Medical AI systems are becoming increasingly accurate, but most remain black boxes.

Clinicians are often presented with a prediction without understanding:

- Why the prediction was made
- What evidence supports it
- How confident the model is
- Whether the recommendation can be trusted

At the same time, modern LLMs can hallucinate medical information, creating serious risks in healthcare environments.

Healthcare professionals need AI systems that are:

- Accurate
- Explainable
- Evidence-backed
- Clinically useful
- Secure
- Fast enough for real-world workflows

---

## The Solution

AI Medical Assistant combines:

- Computer Vision
- Retrieval-Augmented Generation (RAG)
- Explainable AI
- Clinical Decision Support

into a unified healthcare platform.

Instead of simply predicting a diagnosis, the system:

1. Analyzes medical scans using specialized AI models
2. Produces confidence-aware diagnostic predictions
3. Generates explainable findings
4. Retrieves supporting medical literature
5. Delivers citation-backed clinical reasoning
6. Recommends appropriate specialists

The result is a transparent AI workflow designed to increase clinician trust and reduce AI hallucinations.

---

## Demo

<p align="center">
  <img src="./assets/dashboard.png" width="100%">
</p>

### Live Application

https://your-demo-link.com

### Video Demonstration

https://youtube.com/watch?v=your-video

---

## Features

### Brain MRI Analysis

AI-powered brain tumor detection and classification.

**Capabilities**

- Tumor classification
- Confidence scoring
- Clinical interpretation
- Diagnostic reporting
- Explainable predictions

---

### Knee Osteoarthritis Assessment

Automated Kellgren-Lawrence grading from X-Ray images.

**Capabilities**

- Severity grading
- Confidence probabilities
- Clinical interpretation
- Progression assessment

---

### Kidney Ultrasound Analysis

Automated kidney morphometry and anomaly assessment.

**Capabilities**

- Morphometric measurements
- Structure evaluation
- Anomaly detection
- Structured reporting

---

### Grounded Medical Consultation

Unlike traditional medical chatbots, responses are generated using retrieved medical evidence.

**Sources**

- PubMed
- WHO Guidelines
- Clinical Literature
- Medical Knowledge Base

This significantly reduces hallucination risk while improving trustworthiness.

---

### Specialist Recommendation Engine

Based on findings, the system recommends appropriate healthcare specialties:

- Neurology
- Neurosurgery
- Orthopedics
- Nephrology

---

## Model Performance

| Module | Metric |
|----------|----------|
| Brain MRI Classification | XX% Accuracy |
| Knee Osteoarthritis Grading | XX% Macro F1 |
| Kidney Ultrasound Analysis | XX% Accuracy |

---

## Explainability

The platform integrates Grad-CAM visual explanations, allowing healthcare professionals to inspect the image regions influencing model predictions.

This provides transparency beyond traditional black-box AI systems.

---

## Architecture

```text
┌──────────────────────────────────────────────┐
│              React Frontend                  │
│       Clinical Dashboard (Vite SPA)          │
└─────────────────────┬────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────┐
│             FastAPI Backend                  │
│        JWT Authentication Gateway            │
└─────────────────────┬────────────────────────┘
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼

┌────────────────┐ ┌────────────────┐ ┌────────────────┐
│ Brain MRI AI   │ │ Knee X-Ray AI  │ │ Kidney US AI   │
│ Classification │ │ KL Grading     │ │ Morphometry    │
└───────┬────────┘ └───────┬────────┘ └───────┬────────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           ▼

┌──────────────────────────────────────────────┐
│       Retrieval-Augmented Reasoning          │
│          LangChain + Mistral AI              │
└─────────────────────┬────────────────────────┘
                      │
                      ▼

┌──────────────────────────────────────────────┐
│          ChromaDB Knowledge Base             │
│      PubMed + WHO + Clinical Literature      │
└──────────────────────────────────────────────┘
```

---

## Technology Stack

| Layer | Technology |
|---------|---------|
| Frontend | React, Vite, Framer Motion |
| Backend | FastAPI |
| Vision AI | PyTorch, Torchvision |
| RAG | LangChain, ChromaDB |
| LLM | Mistral AI |
| Authentication | Supabase |
| Deployment | Docker |

---

## Impact

AI Medical Assistant helps healthcare professionals:

- Reduce diagnostic delays
- Improve clinical confidence
- Access evidence-backed explanations
- Minimize hallucinated medical advice
- Increase transparency through explainable AI

---

## Future Roadmap

- DICOM support
- Expanded imaging modalities
- Clinical PDF generation
- Multi-language consultation
- Longitudinal patient monitoring
- Physician dashboard



---

## Disclaimer

> AI Medical Assistant is a Clinical Decision Support (CDS) platform developed for educational, research, and demonstration purposes. It is not a medical device and should not replace professional medical judgment, diagnosis, or treatment. All outputs must be reviewed and validated by qualified healthcare professionals before clinical use.

---

## License

MIT License
