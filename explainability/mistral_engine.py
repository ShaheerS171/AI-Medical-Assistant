import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class MedicalExplainerAPI:

  def __init__(self, api_key: str = None, model_name: str = None):
    key = api_key or os.getenv("MISTRAL_API_KEY")
    if not key:
      raise ValueError("MISTRAL_API_KEY is not set in environment or .env file.")

    # Fallback to standard Mistral model identifier 'mistral-large-latest' if not specified
    self.model = model_name or os.getenv("MISTRAL_MODEL", "mistral-large-latest")

    # Initialize OpenAI client pointing to Mistral's endpoint
    # We add Accept-Encoding to prevent a known httpx bug with brotli decompression
    self.client = OpenAI(
        api_key=key, 
        base_url="https://api.mistral.ai/v1",
        default_headers={"Accept-Encoding": "gzip, deflate"}
    )

  def generate_tumor_report(
      self,
      predicted_class: str,
      confidence: float,
      area_mm2: float = None,
      area_cm2: float = None,
  ) -> str:
    area_info = (
        f"{area_mm2:.1f} mm² ({area_cm2:.2f} cm²)"
        if area_mm2
        else "Not detected / Bounding box unavailable"
    )

    prompt = f"""
You are an AI Clinical Assistant evaluating automated MRI brain scan vision model outputs.

### MRI Findings:
- Detected Category: {predicted_class.upper()}
- Vision Model Confidence: {confidence * 100:.1f}%
- Estimated Tumor Region Area: {area_info}

Please generate a professional radiological draft organized strictly under these 4 sections:

1. **Condition Overview & Severity Assessment**: Explain what a {predicted_class} is and assess the potential severity based on the measured physical size ({area_info}).
2. **Clinical Implications & Risks**: Detail potential symptoms or neurological impacts (e.g., pressure on adjacent brain structures, headaches, motor disruption).
3. **Precautionary Measures**: Immediate safety steps for patient management and monitoring.
4. **Recommended Diagnostic Follow-Ups**: Specific next clinical steps (e.g., contrast T1-weighted MRI, biopsy, neurosurgical consultation).

Keep the response authoritative, clear, and structured for medical presentation.
"""

    response = self.client.chat.completions.create(
        model=self.model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional medical reasoning AI specialized in"
                    " neuro-radiology explanations."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content

  def generate_knee_report(
      self, predicted_grade: int, confidence: float = 0.0
  ) -> str:
    kl_descriptions = {
        0: "Grade 0 (None) - Normal knee joint structure with no signs of osteoarthritis.",
        1: "Grade 1 (Doubtful) - Doubtful joint space narrowing and possible osteophytic liping.",
        2: "Grade 2 (Minimal) - Definite osteophytes and possible joint space narrowing.",
        3: "Grade 3 (Moderate) - Moderate multiple osteophytes, definite narrowing of joint space, and some sclerosis.",
        4: "Grade 4 (Severe) - Large osteophytes, marked joint space narrowing, severe sclerosis, and definite deformity of bone ends.",
    }

    grade_desc = kl_descriptions.get(
        predicted_grade, f"KL Grade {predicted_grade}"
    )

    prompt = f"""
You are an AI Clinical Assistant evaluating automated knee radiograph (X-ray) classification outputs.

### Radiograph Findings:
- Assessed Severity: Kellgren-Lawrence (KL) Grade {predicted_grade}
- Classification Confidence: {confidence * 100:.1f}%
- Standard Description: {grade_desc}

Please generate a professional orthopedic report organized strictly under these 4 sections:

1. **Pathological Interpretation**: Explain the radiological meaning of KL Grade {predicted_grade} regarding joint cartilage loss and bone changes.
2. **Functional Implications**: Describe typical patient symptoms at this stage (e.g., stiffness, localized pain, mobility restrictions).
3. **Precautionary & Lifestyle Management**: Recommendations for physical care (e.g., weight management, low-impact exercise, joint protection).
4. **Recommended Clinical Next Steps**: Standard interventions (e.g., physical therapy, anti-inflammatory options, orthopedic consult, or weight-bearing imaging).

Keep the response authoritative, clear, and structured for clinical review.
"""

    response = self.client.chat.completions.create(
        model=self.model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional medical reasoning AI specialized in"
                    " orthopedic radiograph explanations."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content