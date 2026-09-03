# React Frontend Conversion Documentation

## Overview

This document describes the migration of the AI Medical Assistant user interface from Streamlit (`frontend.py`) to a modern React-based Single Page Application (SPA) built with Vite.

The conversion focuses exclusively on the frontend layer. No modifications are made to the FastAPI backend (`app.py`), machine learning models, authentication logic, inference pipelines, or business logic.

The React application communicates with the existing FastAPI backend through REST APIs and preserves all functionality available in the Streamlit implementation while providing a more scalable, maintainable, and production-ready user experience.

---

# Objectives

The React frontend is designed to achieve the following goals:

* Replace the Streamlit interface with a modern SPA architecture.
* Preserve feature parity with the existing application.
* Improve responsiveness and user experience.
* Support authentication using Supabase JWT sessions.
* Provide reusable UI components.
* Enable future scalability and deployment.
* Deliver a visually appealing healthcare-focused interface.

---

# Technology Stack

## Core Framework

| Technology       | Purpose                             |
| ---------------- | ----------------------------------- |
| React            | Frontend UI framework               |
| Vite             | Build system and development server |
| React Router DOM | Client-side routing                 |
| Axios            | API communication                   |
| Framer Motion    | Animations and transitions          |
| React Toastify   | User notifications                  |
| Supabase JS SDK  | Authentication                      |
| React Markdown   | Safe rendering of generated reports |
| Lucide React     | Icon system                         |

---

# Project Structure

```text
frontend/
├── index.html
├── package.json
├── vite.config.js
├── src/
│
├── main.jsx
├── App.jsx
├── index.css
│
├── api/
│   └── client.js
│
├── context/
│   └── AuthContext.jsx
│
├── components/
│   ├── Sidebar.jsx
│   ├── MetricCard.jsx
│   ├── ReportBox.jsx
│   ├── CitationPopover.jsx
│   └── PatientForm.jsx
│
└── pages/
    ├── LoginPage.jsx
    ├── BrainMRIPage.jsx
    ├── KneeXRayPage.jsx
    ├── ChatbotPage.jsx
    └── KidneyUltrasoundPage.jsx
```

---

# Application Architecture

```text
+---------------------------------------------------+
|                 React Frontend                    |
|                                                   |
|  React Router                                     |
|       │                                           |
|       ▼                                           |
|  Feature Pages                                    |
|       │                                           |
|       ▼                                           |
|  Axios API Client                                 |
|       │                                           |
|       ▼                                           |
|  FastAPI Backend                                  |
|       │                                           |
|       ├── Brain MRI Inference                     |
|       ├── Knee OA Inference                       |
|       ├── Kidney Ultrasound Analysis              |
|       ├── Medical Chatbot                         |
|       └── Doctor Finder                           |
+---------------------------------------------------+
```

---

# Authentication Flow

## Authentication Provider

Authentication is handled through Supabase.

### Process

1. User signs in or registers.
2. Supabase returns an authenticated session.
3. JWT token is stored in local storage.
4. AuthContext maintains global session state.
5. Axios automatically attaches the JWT to requests.
6. Backend validates the JWT for protected endpoints.

### Authorization Header

```http
Authorization: Bearer <JWT_TOKEN>
```

---

# API Client

## File

```text
src/api/client.js
```

### Responsibilities

* Create a centralized Axios instance.
* Configure backend base URL.
* Attach JWT tokens automatically.
* Handle authentication failures.
* Simplify API communication across pages.

### Request Flow

```text
Page
  ↓
Axios Client
  ↓
JWT Interceptor
  ↓
FastAPI Endpoint
  ↓
Response
  ↓
React Component
```

---

# Routing

## Route Configuration

| Route              | Component            |
| ------------------ | -------------------- |
| /login             | LoginPage            |
| /brain-mri         | BrainMRIPage         |
| /knee-xray         | KneeXRayPage         |
| /chatbot           | ChatbotPage          |
| /kidney-ultrasound | KidneyUltrasoundPage |

---

# Feature Modules

## Brain MRI Tumor Detection

### Page

```text
BrainMRIPage.jsx
```

### Purpose

Provides MRI-based tumor classification and diagnostic analysis.

### Endpoint

```http
POST /predict/brain-mri
```

### Workflow

1. Upload MRI image.
2. Submit image to backend.
3. Receive prediction results.
4. Display:

   * Tumor classification
   * Confidence score
   * Diagnostic interpretation
   * Supporting metrics
5. Allow result export.

### Output Components

* MetricCard
* ReportBox
* Result Summary Panel

---

## Knee Osteoarthritis Detection

### Page

```text
KneeXRayPage.jsx
```

### Endpoint

```http
POST /predict/knee-xray
```

### Workflow

1. Upload X-ray image.
2. Send image to inference endpoint.
3. Receive KL grading prediction.
4. Display:

   * OA severity grade
   * Confidence score
   * Clinical interpretation

### Output Components

* MetricCard
* ReportBox

---

## Kidney Ultrasound Morphometry

### Page

```text
KidneyUltrasoundPage.jsx
```

### Endpoint

```http
POST /predict/kidney-ultrasound
```

### Workflow

1. Upload ultrasound image.
2. Submit image for analysis.
3. Receive kidney measurements.
4. Display:

   * Morphometric metrics
   * Diagnostic insights
   * Structured findings

---

## Medical Chatbot

### Page

```text
ChatbotPage.jsx
```

### Endpoint

```http
POST /consult
```

### Features

* Medical question answering
* Symptom guidance
* Health recommendations
* Urgency classification

### Workflow

1. User enters question.
2. Request sent to chatbot endpoint.
3. Response displayed.
4. Urgency badge rendered.

---

## Doctor Finder

### Page

```text
ChatbotPage.jsx
```

### Endpoint

```http
GET /find-doctors
```

### Workflow

1. User enters location.
2. Backend returns nearby doctors.
3. Results displayed as cards.

---

# Shared Components

## Sidebar

### File

```text
components/Sidebar.jsx
```

### Responsibilities

* Navigation
* Route switching
* Mobile responsiveness
* User profile display

---

## MetricCard

### File

```text
components/MetricCard.jsx
```

### Responsibilities

Display numerical metrics including:

* Confidence scores
* Measurements
* Predictions
* Risk levels

---

## ReportBox

### File

```text
components/ReportBox.jsx
```

### Responsibilities

Display generated diagnostic content and structured findings.

---

## CitationPopover

### File

```text
components/CitationPopover.jsx
```

### Responsibilities

Display supporting references and citations when available.

---

## PatientForm

### File

```text
components/PatientForm.jsx
```

### Responsibilities

Collect patient metadata and diagnostic inputs.

---

# Design System

## Color Palette

### Primary Background

```css
#0F1B2D
```

### Accent

```css
#00D4B4
```

### Text

```css
#E8F4FD
```

---

## Typography

### Font Family

```css
Inter
```

Imported through Google Fonts.

---

# Visual Design Principles

## Glass Morphism

Used for:

* Sidebar panels
* Results containers
* Information cards

Example characteristics:

```css
backdrop-filter: blur()
rgba transparency
soft shadows
rounded borders
```

---

## Animation System

Implemented using Framer Motion.

### Features

* Page transitions
* Fade-in animations
* Staggered card reveals
* Loading indicators
* Interactive hover effects

---

## Responsive Design

### Desktop

* Fixed navigation sidebar
* Multi-column layout

### Tablet

* Collapsible sidebar
* Adaptive content spacing

### Mobile

* Bottom navigation
* Single-column layout
* Touch-optimized controls

---

# Result Presentation Strategy

Because the existing FastAPI backend does not expose a dedicated report-generation endpoint:

## Current Approach

1. Call prediction endpoint.
2. Receive structured prediction data.
3. Display results using React components.
4. Render metrics and interpretations directly.

This preserves all functionality already available in the backend.

---

# PDF Export Strategy

The current backend does not expose a standalone PDF export API.

## Frontend Solution

The React application provides a printable report view.

Workflow:

```text
Prediction Result
      ↓
Formatted Report View
      ↓
window.print()
      ↓
Save as PDF
```

This maintains export capability without backend modifications.

---

# Development Environment

## Backend

```bash
cd /home/shaheer/python/AI-Medical-Assistant

uvicorn app:app --reload --port 8000
```

Backend URL:

```text
http://localhost:8000
```

---

## Frontend

```bash
cd frontend

npm install

npm run dev
```

Frontend URL:

```text
http://localhost:5173
```

---

# Verification Checklist

## Authentication

* Login page loads correctly.
* User registration succeeds.
* JWT token stored successfully.
* Protected routes require authentication.

---

## Brain MRI Module

* Image upload works.
* API request succeeds.
* Prediction results render.
* Metrics display correctly.

---

## Knee Osteoarthritis Module

* X-ray upload succeeds.
* Prediction returned successfully.
* KL grading displayed correctly.

---

## Kidney Ultrasound Module

* Ultrasound upload succeeds.
* Measurements render correctly.
* Findings appear in result panel.

---

## Medical Chatbot

* Question submission works.
* Responses render correctly.
* Urgency indicators display properly.

---

## Doctor Finder

* Location search works.
* Doctor list renders successfully.
* Results remain responsive across devices.

---

# Deployment Readiness

The React frontend is designed for deployment on modern hosting platforms including:

* Vercel
* Netlify
* AWS Amplify
* Cloudflare Pages
* Self-hosted Nginx environments

No backend modifications are required for deployment beyond configuring the API base URL and CORS settings.

---

# Conclusion

The React frontend conversion modernizes the AI Medical Assistant user experience while preserving complete compatibility with the existing FastAPI backend. The architecture introduces reusable components, responsive layouts, animation support, secure authentication integration, and scalable frontend practices suitable for production deployment.
