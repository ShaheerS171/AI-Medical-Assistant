import io
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from PIL import Image

from knee_model.src.inference import KneeOAPredictor
from knee_model.src.gradcam import run_gradcam as knee_gradcam
from tumor_model.src.inference import BrainTumorPredictor

models_pipeline = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    models_pipeline["knee"] = KneeOAPredictor(
        checkpoint_path="knee_model/models/knee_ordinal_best.pth",
        metadata_path="knee_model/run_metadata.json"
    )
    models_pipeline["brain"] = BrainTumorPredictor(
        yolo_path="tumor_model/modelfiles/tumorbestyolo.pt",
        cls_path="tumor_model/modelfiles/MRIb3.pth"
    )
    yield
    models_pipeline.clear()


app = FastAPI(title="Unified Medical AI Assistant API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def read_image(file: UploadFile) -> Image.Image:
    try:
        contents = file.file.read()
        return Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")


@app.get("/")
def root():
    return {"status": "online", "message": "Unified Medical AI Assistant API Operational"}


# -----------------------------------------------------------------------------
# Knee Osteoarthritis Endpoints
# -----------------------------------------------------------------------------
@app.post("/knee/predict")
def knee_predict(file: UploadFile = File(...)):
    image = read_image(file)
    return models_pipeline["knee"].predict(image)


@app.post("/knee/explain")
def knee_explain(file: UploadFile = File(...)):
    image = read_image(file)
    predictor = models_pipeline["knee"]
    res = predictor.predict(image)
    overlay, _ = knee_gradcam(predictor.model, image, res["predicted_grade"], device=predictor.device)
    
    buf = io.BytesIO()
    overlay.save(buf, format="JPEG")
    return Response(content=buf.getvalue(), media_type="image/jpeg")


# -----------------------------------------------------------------------------
# Brain Tumor Endpoints
# -----------------------------------------------------------------------------
@app.post("/brain/predict")
def brain_predict(file: UploadFile = File(...), mm_per_pixel: float = 0.5):
    image = read_image(file)
    res = models_pipeline["brain"].predict(image, mm_per_pixel=mm_per_pixel)
    return {
        "predicted_class": res["predicted_class"],
        "confidence": res["confidence"],
        "probabilities": res["probabilities"],
        "tumor_area_pixels": res["tumor_area_pixels"],
        "tumor_area_mm2": res["tumor_area_mm2"],
        "tumor_area_cm2": res["tumor_area_cm2"],
        "bounding_box": res["bounding_box"]
    }


@app.post("/brain/explain-cam")
def brain_cam(file: UploadFile = File(...)):
    image = read_image(file)
    predictor: BrainTumorPredictor = models_pipeline["brain"]
    res = predictor.predict(image)
    cam_img = predictor.generate_gradcam(image, res["cls_tensor"], res["pred_idx"])
    
    buf = io.BytesIO()
    cam_img.save(buf, format="JPEG")
    return Response(content=buf.getvalue(), media_type="image/jpeg")


@app.post("/brain/explain-detection")
def brain_detection(file: UploadFile = File(...)):
    image = read_image(file)
    predictor: BrainTumorPredictor = models_pipeline["brain"]
    res = predictor.predict(image)
    det_img = predictor.generate_detection_overlay(res["det_result"])
    
    buf = io.BytesIO()
    det_img.save(buf, format="JPEG")
    return Response(content=buf.getvalue(), media_type="image/jpeg")