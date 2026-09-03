from pydantic import BaseModel
from typing import Dict, Any, Optional

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
