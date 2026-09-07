# React Frontend Documentation

## Overview

The AI Medical Assistant user interface is a responsive, clinical-grade Single Page Application (SPA) built with **React**, **Vite**, and **Framer Motion**. 

The frontend connects directly to the unified **FastAPI** backend (`app.py`) via a centralized Axios API client (`src/api/client.js`) and leverages **Supabase** JWT tokens for secure authentication and route protection.

The platform provides dedicated modules for four diagnostic vision modalities, a retrieval-augmented medical consultation chatbot, a geolocation-based doctor finder, automated LLM radiological report previewing, and server-side PDF generation.

---

# Technology Stack

| Technology | Role / Purpose |
|---|---|
| **React 18** | Component-driven UI framework |
| **Vite** | Fast HMR build tool and development server |
| **Framer Motion** | Micro-interactions, animated transitions, loading overlays |
| **Axios** | HTTP client with automatic JWT bearer token interceptors |
| **Supabase JS SDK** | User authentication and session persistence |
| **React Markdown** | Safe rendering of 5-section AI radiological reports |
| **Lucide React** | Medical and operational icon system (`Brain`, `Bone`, `ScanHeart`, `Activity`, etc.) |
| **React Toastify** | Feedback notifications and toast alerts |

---

# Project Structure

```text
frontend/
├── index.html
├── package.json
├── vite.config.js
├── src/
│   ├── main.jsx                   # React root mount point
│   ├── App.jsx                    # Application shell, state router, and toast provider
│   ├── App.css                    # App-level styling
│   ├── index.css                  # Design system, themes, and responsive utility styles
│   │
│   ├── api/
│   │   └── client.js              # Central Axios instance with Supabase JWT interceptors
│   │
│   ├── context/
│   │   └── AuthContext.jsx        # Supabase authentication state and session lifecycle
│   │
│   ├── components/
│   │   ├── Sidebar.jsx            # Desktop & mobile diagnostic navigation menu
│   │   └── UploadZone.jsx         # Drag-and-drop image file uploader with preview
│   │
│   └── pages/
│       ├── LoginPage.jsx          # Supabase sign-in and sign-up form
│       ├── BrainMRIPage.jsx       # Brain MRI tumor detection & lesion quantification
│       ├── KneeXRayPage.jsx       # Knee radiograph osteoarthritis KL grading
│       ├── TuberculosisPage.jsx   # Chest X-ray Pulmonary Tuberculosis screening
│       ├── KidneyUltrasoundPage.jsx # Kidney ultrasound morphometric measurement
│       └── ChatbotPage.jsx        # Grounded consultation & LocationIQ doctor finder
```

---

# Application State & Navigation

Instead of heavy external routing dependencies, the core application shell (`App.jsx`) utilizes a clean, animated tab-navigation router pattern:

```jsx
const PAGE_MAP = {
  brain: BrainMRIPage,
  knee: KneeXRayPage,
  tb: TuberculosisPage,
  chat: ChatbotPage,
  kidney: KidneyUltrasoundPage,
};
```

### Navigation Items in `Sidebar.jsx`:
1. **Brain MRI** (`id: 'brain'`) — Tumor Detection & Segmentation
2. **Knee X-Ray** (`id: 'knee'`) — Kellgren-Lawrence Osteoarthritis Severity
3. **Chest X-Ray** (`id: 'tb'`) — Pulmonary Tuberculosis Screening
4. **Medical Consultation** (`id: 'chat'`) — Evidence-based Consultation & Doctor Finder
5. **Kidney Ultrasound** (`id: 'kidney'`) — DeepLabV3+ Morphometric Measurement

---

# Authentication Architecture

Authentication is managed via `src/context/AuthContext.jsx` interfacing with Supabase:

1. **Sign-In / Sign-Up**: Handled in `LoginPage.jsx` via `supabase.auth.signInWithPassword` or `signUp`.
2. **Session Persistence**: Stored in `localStorage` as `auth_token`.
3. **Axios Interceptor**:
   ```javascript
   // src/api/client.js
   client.interceptors.request.use((config) => {
       const token = localStorage.getItem('auth_token');
       if (token) config.headers['Authorization'] = `Bearer ${token}`;
       return config;
   });
   ```
4. **Route Guard**: `AppInner` in `App.jsx` intercepts unauthenticated sessions and renders `LoginPage` until a valid session is verified.

---

# Feature Modules & Workflows

## 1. Chest X-Ray — Tuberculosis Screening
- **Component**: `src/pages/TuberculosisPage.jsx`
- **Inference Route**: `POST /predict/tb-xray` (multipart form: `file`, `age`, `sex`)
- **Report Route**: `POST /generate/report` (modality: `tb-xray`)
- **PDF Export**: `POST /export/pdf`
- **Workflow & UI Elements**:
  - Drag-and-drop chest X-ray uploader.
  - Patient intake form: Full Name, Patient ID, Age, Biological Sex, and Clinical Symptoms.
  - Animated analysis spinner during DenseNet121 inference & Grad-CAM generation.
  - Side-by-side visual comparison: Original Chest X-Ray vs. Grad-CAM Saliency Overlay.
  - Diagnostic metrics:
    - Primary Diagnosis (`Normal` / `Tuberculosis`) with conditional color badges.
    - Confidence Percentage.
    - Class Probabilities breakdown (`Normal: %`, `Tuberculosis: %`).
  - Formatted 5-section radiological report preview rendered in `ReactMarkdown`.
  - Offline structured fallback report generator if LLM API is unavailable.
  - "Download PDF Report" action generating an official signed medical document.

---

## 2. Brain MRI — Tumor Detection & Quantification
- **Component**: `src/pages/BrainMRIPage.jsx`
- **Inference Route**: `POST /predict/brain-mri`
- **Report Route**: `POST /generate/report` (modality: `brain-mri`)
- **PDF Export**: `POST /export/pdf`
- **Workflow & UI Elements**:
  - Upload of brain MRI axial slices.
  - Patient intake metadata collection.
  - Dual visual overlays: Grad-CAM attention heatmap and YOLO lesion bounding boxes.
  - Lesion surface area metrics (`mm²` and `cm²`).
  - 5-section neuro-radiological report generation and PDF download.

---

## 3. Knee Radiograph — Osteoarthritis Grading
- **Component**: `src/pages/KneeXRayPage.jsx`
- **Inference Route**: `POST /predict/knee-xray`
- **Report Route**: `POST /generate/report` (modality: `knee-xray`)
- **PDF Export**: `POST /export/pdf`
- **Workflow & UI Elements**:
  - Upload of knee AP radiograph.
  - Kellgren-Lawrence (KL Grade 0 to 4) severity assessment.
  - Temperature-scaled calibration status indicator.
  - Grad-CAM joint space and osteophyte attention heatmap.
  - Clinical report generation and PDF export.

---

## 4. Kidney Ultrasound — Morphometry
- **Component**: `src/pages/KidneyUltrasoundPage.jsx`
- **Inference Route**: `POST /predict/kidney-ultrasound` (accepts longitudinal and transverse views)
- **Report Route**: `POST /generate/report` (modality: `kidney-ultrasound`)
- **PDF Export**: `POST /export/pdf`
- **Workflow & UI Elements**:
  - Dual ultrasound image uploader (Coronal/Longitudinal and Transverse).
  - DeepLabV3+ segmented contour overlays.
  - Calculated dimensions: Length (cm), Width (cm), and Thickness (cm).
  - Normal adult reference comparisons and nephromegaly/atrophy assessment.

---

## 5. Evidence-Grounded Consultation & Doctor Finder
- **Component**: `src/pages/ChatbotPage.jsx`
- **Consult Route**: `POST /consult` (symptoms, optional PDF report upload)
- **Doctor Route**: `GET /find-doctors` (location, specialty, radius)
- **Workflow & UI Elements**:
  - Multi-turn conversational interface with typing indicators.
  - RAG-powered responses with verified medical citations and urgency triage tags.
  - Interactive doctor finder powered by LocationIQ: searches for nearby specialists, hospitals, and clinics with distance calculations.

---

# PDF Report Generation Pipeline

The frontend requests formal PDF reports by sending diagnostic data directly to the backend's `/export/pdf` endpoint:

```javascript
const req = {
    patient_name: form.name,
    patient_id: form.id,
    patient_age: Number(form.age),
    patient_sex: form.sex,
    patient_history: form.history,
    report_text: results.report,
    scan_type: "Chest X-Ray (Tuberculosis Screening)",
    original_img_b64: base64OriginalImage,
    overlay_img_b64: results.gradcam_b64 || "",
    metrics: {
        "Diagnosis": results.predicted_class,
        "Confidence": `${(results.confidence * 100).toFixed(1)}%`,
        "Probabilities": `TB: ${tbProb} | Normal: ${normProb}`
    }
};

const res = await client.post('/export/pdf', req, { responseType: 'blob' });
```

The backend compiles an in-memory PDF via ReportLab, returning a binary blob that is downloaded directly in the user's browser.

---

# Running and Building the Frontend

### Development Mode
```bash
cd frontend
npm install
npm run dev
```
Default local URL: `http://localhost:5173`

### Production Build
```bash
cd frontend
npm run build
```
Generates optimized static assets in `frontend/dist/` ready for deployment on Vercel, Netlify, AWS S3/CloudFront, or Nginx.
