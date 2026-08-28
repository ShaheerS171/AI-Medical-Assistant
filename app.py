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
from typing import Optional, List, Dict, Any
from PIL import Image

from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Internal module imports
from knee_model.src.inference import KneeOAPredictor
from knee_model.src.gradcam import run_gradcam
from tumor_model.src.inference import BrainTumorPredictor
from explainability.mistral_engine import MedicalExplainerAPI
from explainability.pdf_generator import MedicalReportPDFGenerator
from chatbot.engine import run_consult_logic, find_doctors_logic

app = FastAPI(title="AI Medical Assistant Unified API")

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


class KneeXRayPredictionResponse(BaseModel):
    predicted_grade: int
    confidence: float
    calibrated: bool


class ConsultResponse(BaseModel):
    advice: str
    urgency: str
    recommended_specialist: Optional[str] = None
    disclaimer: str


class Doctor(BaseModel):
    name: str
    address: Optional[str] = None
    distance_km: Optional[float] = None
    lat: Optional[float] = None
    lon: Optional[float] = None


class DoctorSearchResponse(BaseModel):
    results: List[Doctor]


# ---------------------------------------------------------------------------
# System Endpoints
# ---------------------------------------------------------------------------

@app.get("/")
def home():
    return {"message": "Welcome to the AI-Medical Assistant Platform"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "AI Medical Assistant API"}


# ---------------------------------------------------------------------------
# Vision Diagnostic Endpoints
# ---------------------------------------------------------------------------
@app.post("/predict/brain-mri", response_model=BrainMRIPredictionResponse)
async def predict_brain_mri(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

    contents = await file.read()
    image = Image.open(io.BytesIO(contents)).convert("RGB")

    try:
        predictor = get_tumor_predictor()
        res = predictor.predict(image)
        return BrainMRIPredictionResponse(
            predicted_class=res["predicted_class"],
            confidence=float(res["confidence"]),
            tumor_area_mm2=res.get("tumor_area_mm2"),
            tumor_area_cm2=res.get("tumor_area_cm2")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Brain MRI processing failed: {str(e)}")


@app.post("/predict/knee-xray", response_model=KneeXRayPredictionResponse)
async def predict_knee_xray(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

    contents = await file.read()
    image = Image.open(io.BytesIO(contents)).convert("RGB")

    try:
        predictor = get_knee_predictor()
        res = predictor.predict(image)
        return KneeXRayPredictionResponse(
            predicted_grade=int(res["predicted_grade"]),
            confidence=float(res["confidence"]),
            calibrated=bool(res["calibrated"])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Knee X-Ray processing failed: {str(e)}")


# ---------------------------------------------------------------------------
# Chatbot & Doctor Finder Endpoints
# ---------------------------------------------------------------------------
@app.post("/consult", response_model=ConsultResponse)
async def consult(
    symptoms: str = Form(""),
    file: Optional[UploadFile] = File(None),
    api_key: Optional[str] = Form(None),
    x_api_key: Optional[str] = Header(None, alias="X-Mistral-Api-Key"),
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
def find_doctors(location: str, specialty: Optional[str] = None, radius_km: float = 15.0):
    if not location:
        raise HTTPException(status_code=400, detail="Location is required.")

    try:
        doctors = find_doctors_logic(location, specialty, radius_km)
        return DoctorSearchResponse(results=[Doctor(**d) for d in doctors])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))