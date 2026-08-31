import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class MedicalExplainerAPI:
    """
    Interfaces with Mistral AI to generate structured 5-section radiology 
    and orthopedic clinical reports based on computer vision inference outputs 
    and patient metadata.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        key = api_key or os.getenv("MISTRAL_API_KEY")
        if not key:
            raise ValueError("MISTRAL_API_KEY is not set in environment or .env file.")

        self.model = model_name or os.getenv("MISTRAL_MODEL", "mistral-large-latest")

        self.client = OpenAI(
            api_key=key,
            base_url="https://api.mistral.ai/v1",
            default_headers={"Accept-Encoding": "gzip, deflate"}
        )

    def generate_tumor_report(
        self,
        predicted_class: str,
        confidence: float,
        patient_info: Optional[Dict[str, Any]] = None,
        area_mm2: Optional[float] = None,
        area_cm2: Optional[float] = None,
    ) -> str:
        patient_info = patient_info or {}
        patient_name = patient_info.get("name", "Unspecified")
        patient_id = patient_info.get("id", "N/A")
        age = patient_info.get("age", "Unspecified")
        sex = patient_info.get("sex", "Unspecified")
        history = patient_info.get("history", "No clinical history provided.")

        area_info = (
            f"{area_mm2:.1f} mm² ({area_cm2:.2f} cm²)"
            if area_mm2
            else "Not detected / Bounding box unavailable"
        )

        prompt = f"""
You are an expert Neuro-Radiology AI Assistant. Generate a formal 5-section medical report based on the provided patient intake data and automated vision model findings.

### Patient & Examination Header
- Patient Name: {patient_name}
- Patient ID: {patient_id}
- Age / Sex: {age} / {sex}
- Imaging Modality: Brain MRI Scan

### Machine Vision Findings:
- Classified Findings: {predicted_class.upper()}
- Vision Model Confidence: {confidence * 100:.1f}%
- Estimated Lesion Area: {area_info}
- Clinical History / Indication: {history}

Generate a formal medical draft structured strictly under these 5 Markdown section headers:

1. **Patient & Examination Header**
   Summarize patient metadata, scan parameters, and classification confidence metrics.

2. **Clinical History & Indication**
   Synthesize the presented patient history ({history}) and primary clinical indications.

3. **Technique & Visual Observations**
   Describe the visual metrics captured by the model, including the calculated lesion region ({area_info}) and relevant anatomical structures.

4. **Detailed Radiological Findings**
   Provide a clinical assessment of {predicted_class.upper()}, explaining typical imaging characteristics, mass effect, adjacent structure involvement, and pathological significance.

5. **Impression & Clinical Recommendations**
   Deliver a precise summary impression and outline actionable next clinical steps (e.g., contrast-enhanced T1/T2 sequence MRI, neurosurgical evaluation, tissue biopsy).

Keep the language formal, precise, and authoritative.
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a specialized medical reasoning AI generating professional neuro-radiology reports.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )

        return response.choices[0].message.content

    def generate_knee_report(
        self,
        predicted_grade: int,
        confidence: float = 0.0,
        patient_info: Optional[Dict[str, Any]] = None,
    ) -> str:
        patient_info = patient_info or {}
        patient_name = patient_info.get("name", "Unspecified")
        patient_id = patient_info.get("id", "N/A")
        age = patient_info.get("age", "Unspecified")
        sex = patient_info.get("sex", "Unspecified")
        history = patient_info.get("history", "No clinical history provided.")

        kl_descriptions = {
            0: "Grade 0 (None) - Normal knee joint structure with no signs of osteoarthritis.",
            1: "Grade 1 (Doubtful) - Doubtful joint space narrowing and possible osteophytic lipping.",
            2: "Grade 2 (Minimal) - Definite osteophytes and possible joint space narrowing.",
            3: "Grade 3 (Moderate) - Moderate multiple osteophytes, definite joint space narrowing, and subchondral sclerosis.",
            4: "Grade 4 (Severe) - Large osteophytes, marked joint space narrowing, severe sclerosis, and definite deformity of bone ends.",
        }

        grade_desc = kl_descriptions.get(predicted_grade, f"KL Grade {predicted_grade}")

        prompt = f"""
You are an expert Orthopedic Radiology AI Assistant. Generate a formal 5-section medical report based on patient intake data and automated knee radiograph classification.

### Patient & Examination Header
- Patient Name: {patient_name}
- Patient ID: {patient_id}
- Age / Sex: {age} / {sex}
- Imaging Modality: Knee Radiograph (X-Ray)

### Machine Vision Findings:
- Assessed Severity: Kellgren-Lawrence (KL) Grade {predicted_grade}
- Classification Confidence: {confidence * 100:.1f}%
- Diagnostic Criteria: {grade_desc}
- Clinical History / Indication: {history}

Generate a formal medical draft structured strictly under these 5 Markdown section headers:

1. **Patient & Examination Header**
   Summarize patient demographics, imaging modality, assigned KL Grade, and classification confidence.

2. **Clinical History & Indication**
   Synthesize the presented chief complaints ({history}) and orthopedic rationale for evaluation.

3. **Technique & Visual Observations**
   Detail the radiograph observations corresponding to KL Grade {predicted_grade}, evaluating joint space width, marginal osteophytes, and subchondral bone density.

4. **Detailed Radiological Findings**
   Interpret the progression of degenerative joint disease, cartilage integrity loss, and structural alignment alterations.

5. **Impression & Clinical Recommendations**
   Deliver a clear impression and present non-operative or surgical care paths (e.g., targeted physical therapy, weight management, intra-articular therapies, or orthopedic consultation).

Keep the language formal, precise, and authoritative.
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a specialized medical reasoning AI generating professional orthopedic radiology reports.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )

        return response.choices[0].message.content

    def generate_kidney_report(
        self,
        length_cm: float,
        width_cm: float,
        thickness_cm: float,
        patient_info: Optional[Dict[str, Any]] = None,
    ) -> str:
        patient_info = patient_info or {}
        patient_name = patient_info.get("name", "Unspecified")
        patient_id = patient_info.get("id", "N/A")
        age = patient_info.get("age", "Unspecified")
        sex = patient_info.get("sex", "Unspecified")
        history = patient_info.get("history", "No clinical history provided.")

        prompt = f"""
You are an expert Abdominal Radiology AI Assistant. Generate a formal 5-section medical report based on patient intake data and automated kidney ultrasound morphometric measurements.

### Patient & Examination Header
- Patient Name: {patient_name}
- Patient ID: {patient_id}
- Age / Sex: {age} / {sex}
- Imaging Modality: Kidney Ultrasound (B-Mode)

### Machine Vision Findings (DeepLabV3+ Segmentation):
- Kidney Length (Longitudinal View): {length_cm:.2f} cm
- Kidney Width (Transverse View): {width_cm:.2f} cm
- Kidney Thickness (Transverse View): {thickness_cm:.2f} cm
- Clinical History / Indication: {history}

Normal adult kidney morphometry reference:
- Length: 9–12 cm | Width: 4–6 cm | Thickness: 3–5 cm

Generate a formal medical draft structured strictly under these 5 Markdown section headers:

1. **Patient & Examination Header**
   Summarize patient demographics, imaging modality, and examination context.

2. **Clinical History & Indication**
   Synthesize the presented patient history ({history}) and indications for renal ultrasound evaluation.

3. **Technique & Visual Observations**
   Describe the B-mode ultrasound technique and the segmentation-based morphometric measurements obtained: length {length_cm:.2f} cm, width {width_cm:.2f} cm, thickness {thickness_cm:.2f} cm.

4. **Detailed Radiological Findings**
   Interpret the morphometric values in clinical context. Compare against normal adult reference ranges. Discuss whether the kidney is normal, enlarged (nephromegaly), or reduced (renal atrophy), and comment on likely clinical significance (e.g., hydronephrosis, chronic kidney disease, compensatory hypertrophy).

5. **Impression & Clinical Recommendations**
   Deliver a precise impression and outline actionable next steps (e.g., renal function tests, Doppler ultrasound, contrast-enhanced CT, nephrology referral).

Keep the language formal, precise, and authoritative.
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a specialized medical reasoning AI generating professional abdominal radiology reports.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )

        return response.choices[0].message.content