"""
app.py - Unified FastAPI Backend for AI Medical Assistant

Exposes endpoints for:
  1. Diagnostic Vision Models (/predict/brain-mri, /predict/knee-xray)
  2. Report Generation & PDF Exports (/generate/report, /export/pdf)
  3. Chatbot Consultation (/consult)
  4. LocationIQ Doctor & Facility Locator (/find-doctors)

Run with:
    uvicorn app:app --reload --port 8000
"""

import io
import os
import base64
from typing import Optional, List, Dict, Any
from PIL import Image

from fastapi import FastAPI, File, Form, Header, Depends, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Supabase Auth Dependency
from Authentication.fastapi_backend import get_current_user

# Internal module imports
from knee_model.src.inference import KneeOAPredictor
from knee_model.src.gradcam import run_gradcam
from tumor_model.src.inference import BrainTumorPredictor
from kidney_model.src.inference import KidneyUltrasoundPredictor
from explainability.mistral_engine import MedicalExplainerAPI
from explainability.pdf_generator import MedicalReportPDFGenerator
from chatbot.engine import run_consult_logic, find_doctors_logic

app = FastAPI(title="AI Medical Assistant Unified API with Supabase Auth")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Lazy-loaded Predictors & Engines
# ---------------------------------------------------------------------------
_knee_predictor: Optional[KneeOAPredictor] = None
_tumor_predictor: Optional[BrainTumorPredictor] = None
_kidney_predictor: Optional[KidneyUltrasoundPredictor] = None
_explainer_api: Optional[MedicalExplainerAPI] = None
_pdf_generator: Optional[MedicalReportPDFGenerator] = None


def get_knee_predictor() -> KneeOAPredictor:
    global _knee_predictor
    if _knee_predictor is None:
        _knee_predictor = KneeOAPredictor(
            checkpoint_path="knee_model/models/knee_ordinal_best.pth",
            metadata_path="knee_model/run_metadata.json"
        )
    return _knee_predictor


def get_tumor_predictor() -> BrainTumorPredictor:
    global _tumor_predictor
    if _tumor_predictor is None:
        _tumor_predictor = BrainTumorPredictor(
            yolo_path="tumor_model/modelfiles/tumorbestyolo.pt",
            cls_path="tumor_model/modelfiles/MRIb3.pth"
        )
    return _tumor_predictor


def get_kidney_predictor() -> KidneyUltrasoundPredictor:
    global _kidney_predictor
    if _kidney_predictor is None:
        _kidney_predictor = KidneyUltrasoundPredictor(
            weights_path="kidney_model/weights_fixed.pth",
            excel_path="kidney_model/OpenKidneyUltrasoundDataSet_TransducerInfo.xlsx",
        )
    return _kidney_predictor


def get_explainer_api() -> MedicalExplainerAPI:
    global _explainer_api
    if _explainer_api is None:
        _explainer_api = MedicalExplainerAPI()
    return _explainer_api


def get_pdf_generator() -> MedicalReportPDFGenerator:
    global _pdf_generator
    if _pdf_generator is None:
        _pdf_generator = MedicalReportPDFGenerator()
    return _pdf_generator


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------
class PatientInfo(BaseModel):
    name: str = "Jane Doe"
    id: str = "PAT-001"
    age: int = 45
    sex: str = "Female"
    history: str = "No prior history provided."


class BrainMRIPredictionResponse(BaseModel):
    predicted_class: str
    confidence: float
    tumor_area_mm2: Optional[float] = None
    tumor_area_cm2: Optional[float] = None
    gradcam_b64: Optional[str] = None
    overlay_b64: Optional[str] = None


class KneeXRayPredictionResponse(BaseModel):
    predicted_grade: int
    confidence: float
    calibrated: bool
    gradcam_b64: Optional[str] = None


class KidneyUltrasoundResponse(BaseModel):
    length_cm: float
    width_cm: float
    thickness_cm: float


class ConsultResponse(BaseModel):
    advice: str
    urgency: str
    recommended_specialist: Optional[str] = None
    disclaimer: str
    citations: Optional[List[Dict[str, Any]]] = []


class Doctor(BaseModel):
    name: str
    address: Optional[str] = None
    distance_km: Optional[float] = None
    lat: Optional[float] = None
    lon: Optional[float] = None


class DoctorSearchResponse(BaseModel):
    results: List[Doctor]


class PDFExportRequest(BaseModel):
    patient_name: str
    patient_id: str
    patient_age: int
    patient_sex: str
    patient_history: str
    report_text: str
    scan_type: str
    original_img_b64: str
    overlay_img_b64: str
    metrics: Dict[str, Any]


# ---------------------------------------------------------------------------
# System Endpoints
# ---------------------------------------------------------------------------

@app.get("/")
def home():
    return {"message": "Welcome to the AI-Medical Assistant Platform"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "AI Medical Assistant API"}


@app.post("/export/pdf")
def export_pdf(
    req: PDFExportRequest,
    current_user: dict = Depends(get_current_user)
):
    try:
        # Decode base64 images
        # some base64 strings might have data headers like `data:image/png;base64,...`
        # strip it if present
        def decode_img(b64_str):
            if b64_str.startswith("data:"):
                b64_str = b64_str.split(",", 1)[-1]
            # Handle potential empty or missing strings
            if not b64_str:
                img = Image.new('RGB', (100, 100), color=(240, 240, 240))
                return img
            img_data = base64.b64decode(b64_str)
            return Image.open(io.BytesIO(img_data)).convert("RGB")

        orig_img = decode_img(req.original_img_b64)
        over_img = decode_img(req.overlay_img_b64)

        patient_info = {
            "name": req.patient_name,
            "id": req.patient_id,
            "age": req.patient_age,
            "sex": req.patient_sex,
            "history": req.patient_history
        }

        pdf_generator = get_pdf_generator()
        pdf_bytes = pdf_generator.generate_pdf(
            patient_info=patient_info,
            report_text=req.report_text,
            original_img=orig_img,
            overlay_img=over_img,
            metrics=req.metrics,
            scan_type=req.scan_type
        )

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=medical_report_{req.patient_id}.pdf"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


# ---------------------------------------------------------------------------
# Secured Vision Diagnostic Endpoints
# ---------------------------------------------------------------------------
@app.post("/predict/brain-mri", response_model=BrainMRIPredictionResponse)
async def predict_brain_mri(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

    contents = await file.read()
    image = Image.open(io.BytesIO(contents)).convert("RGB")

    try:
        predictor = get_tumor_predictor()
        res = predictor.predict(image)

        # --- Grad-CAM heatmap ---
        gradcam_b64 = None
        try:
            gcam_img = predictor.generate_gradcam(
                image, res["cls_tensor"], res["pred_idx"]
            )
            buf = io.BytesIO()
            gcam_img.save(buf, format="PNG")
            gradcam_b64 = base64.b64encode(buf.getvalue()).decode()
        except Exception:
            pass

        # --- YOLO bounding-box overlay ---
        overlay_b64 = None
        if res.get("det_result") is not None:
            try:
                ov_img = predictor.generate_detection_overlay(res["det_result"])
                buf2 = io.BytesIO()
                ov_img.save(buf2, format="PNG")
                overlay_b64 = base64.b64encode(buf2.getvalue()).decode()
            except Exception:
                pass

        return BrainMRIPredictionResponse(
            predicted_class=res["predicted_class"],
            confidence=float(res["confidence"]),
            tumor_area_mm2=res.get("tumor_area_mm2"),
            tumor_area_cm2=res.get("tumor_area_cm2"),
            gradcam_b64=gradcam_b64,
            overlay_b64=overlay_b64,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Brain MRI processing failed: {str(e)}")


@app.post("/predict/knee-xray", response_model=KneeXRayPredictionResponse)
async def predict_knee_xray(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

    contents = await file.read()
    image = Image.open(io.BytesIO(contents)).convert("RGB")

    try:
        predictor = get_knee_predictor()
        res = predictor.predict(image)

        # --- Grad-CAM cartilage heatmap ---
        gradcam_b64 = None
        try:
            predictor.model.train()  # enable gradients for CAM
            gcam_img, _ = run_gradcam(predictor.model, image, int(res["predicted_grade"]), device=predictor.device)
            predictor.model.eval()
            buf = io.BytesIO()
            gcam_img.save(buf, format="PNG")
            gradcam_b64 = base64.b64encode(buf.getvalue()).decode()
        except Exception:
            if hasattr(predictor, 'model'):
                predictor.model.eval()

        return KneeXRayPredictionResponse(
            predicted_grade=int(res["predicted_grade"]),
            confidence=float(res["confidence"]),
            calibrated=bool(res["calibrated"]),
            gradcam_b64=gradcam_b64,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Knee X-Ray processing failed: {str(e)}")


@app.post("/predict/kidney-ultrasound", response_model=KidneyUltrasoundResponse)
async def predict_kidney_ultrasound(
    longitudinal: UploadFile = File(..., description="Longitudinal (coronal) kidney ultrasound image"),
    transverse: UploadFile = File(..., description="Transverse kidney ultrasound image"),
    current_user: dict = Depends(get_current_user)
):
    for f in (longitudinal, transverse):
        if not f.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail=f"File '{f.filename}' must be an image.")

    long_bytes = await longitudinal.read()
    trans_bytes = await transverse.read()
    long_img = Image.open(io.BytesIO(long_bytes)).convert("RGB")
    trans_img = Image.open(io.BytesIO(trans_bytes)).convert("RGB")

    try:
        predictor = get_kidney_predictor()
        res = predictor.predict(
            longitudinal_img=long_img,
            transverse_img=trans_img,
            long_filename=longitudinal.filename or "unknown",
            trans_filename=transverse.filename or "unknown",
        )
        return KidneyUltrasoundResponse(
            length_cm=res["length_cm"],
            width_cm=res["width_cm"],
            thickness_cm=res["thickness_cm"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kidney ultrasound processing failed: {str(e)}")


# ---------------------------------------------------------------------------
# Secured Chatbot & Doctor Finder Endpoints
# ---------------------------------------------------------------------------
@app.post("/consult", response_model=ConsultResponse)
async def consult(
    symptoms: str = Form(""),
    file: Optional[UploadFile] = File(None),
    api_key: Optional[str] = Form(None),
    x_api_key: Optional[str] = Header(None, alias="X-Mistral-Api-Key"),
    current_user: dict = Depends(get_current_user)
):
    if not symptoms and not file:
        raise HTTPException(status_code=400, detail="Provide symptoms text, an uploaded report, or both.")

    file_bytes = None
    content_type = ""
    if file is not None:
        file_bytes = await file.read()
        content_type = file.content_type or ""

    effective_key = api_key or x_api_key

    try:
        res = run_consult_logic(symptoms, file_bytes, content_type, api_key=effective_key)
        return ConsultResponse(**res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/find-doctors", response_model=DoctorSearchResponse)
def find_doctors(
    location: str,
    specialty: Optional[str] = None,
    radius_km: float = 15.0,
    current_user: dict = Depends(get_current_user)
):
    if not location:
        raise HTTPException(status_code=400, detail="Location is required.")

    try:
        doctors = find_doctors_logic(location, specialty, radius_km)
        return DoctorSearchResponse(results=[Doctor(**d) for d in doctors])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
