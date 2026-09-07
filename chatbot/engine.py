"""
chatbot/engine.py - Core logic for Medical Assistant chatbot and doctor locator.
"""

import base64
import json
import os
import re
from math import atan2, cos, radians, sin, sqrt
from typing import Optional, List, Dict, Any

import requests
from dotenv import load_dotenv

# PubMed RAG — live citation fetcher
from chatbot.pubmed_rag import get_pubmed_citations

load_dotenv()

MISTRAL_CHAT_URL = "https://api.mistral.ai/v1/chat/completions"
MISTRAL_OCR_URL = "https://api.mistral.ai/v1/ocr"

def get_text_model() -> str:
    return (
        os.getenv("LLM_MODEL")
        or os.getenv("DEEPSEEK_MODEL")
        or ("deepseek-chat" if (os.getenv("DEEPSEEK_API_KEY") or os.getenv("LLM_API_KEY")) else os.getenv("MISTRAL_MODEL", "mistral-small-latest"))
    )

def get_vision_model() -> str:
    return (
        os.getenv("VISION_MODEL")
        or os.getenv("MISTRAL_VISION_MODEL")
        or "pixtral-12b-2409"
    )

MEDICAL_SYSTEM_PROMPT = """You are a cautious medical information assistant embedded in a health app.
You are NOT a doctor and must never claim to give a diagnosis.

Given a patient's described symptoms and/or an uploaded medical report (image or PDF, the
latter already converted to text for you), do the following:
1. Summarize what you observe in plain, reassuring language.
2. Suggest general, safe precautions or self-care steps (nothing prescriptive like exact drug dosages).
3. Rate urgency as one of: "low", "medium", "high" ("high" = seek care immediately / emergency room).
4. Recommend a specialist type to see if relevant (e.g. "cardiologist", "dermatologist"), or null if a general physician / no visit is needed.
5. Always make clear this is not a diagnosis and a licensed physician should confirm.
6. If relevant medical literature is provided below, use it to ground your advice and reference it naturally
   (e.g. "According to recent literature..."). Do NOT make up citations.

Respond ONLY with a single JSON object and nothing else (no markdown fences, no preamble), using exactly these keys:
{
  "advice": "<string, a few sentences>",
  "urgency": "<low|medium|high>",
  "recommended_specialist": "<string or null>",
  "disclaimer": "<string>"
}
"""

DEFAULT_DISCLAIMER = "This is not a medical diagnosis. Please consult a licensed physician."
HTTP_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MedicalAssistantApp/1.0"}


def get_llm_api_key(custom_key: Optional[str] = None) -> Optional[str]:
    if custom_key and custom_key.strip():
        return custom_key.strip()
    for env_var in ("LLM_API_KEY", "DEEPSEEK_API_KEY", "MISTRAL_API_KEY", "OPENAI_API_KEY"):
        val = os.getenv(env_var)
        if val and val.strip():
            return val.strip()
    return None

# Keep backwards-compatible alias
get_mistral_api_key = get_llm_api_key


def get_llm_chat_url() -> str:
    # If custom endpoint or base URL provided
    if os.getenv("LLM_CHAT_URL"):
        return os.getenv("LLM_CHAT_URL").strip()
    base_url = os.getenv("LLM_BASE_URL") or os.getenv("DEEPSEEK_BASE_URL")
    if base_url:
        return f"{base_url.rstrip('/')}/chat/completions"
    if os.getenv("DEEPSEEK_API_KEY") or os.getenv("LLM_API_KEY"):
        return "https://api.deepseek.com/v1/chat/completions"
    if os.getenv("MISTRAL_API_KEY"):
        return "https://api.mistral.ai/v1/chat/completions"
    return "https://api.deepseek.com/v1/chat/completions"


def get_llm_headers(custom_key: Optional[str] = None) -> dict:
    key = get_llm_api_key(custom_key)
    if not key:
        raise ValueError("LLM API Key is missing. Please set LLM_API_KEY (or DEEPSEEK_API_KEY / MISTRAL_API_KEY) in .env or app settings.")
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

# Keep backwards-compatible alias
_mistral_headers = get_llm_headers


def _extract_json(raw_text: str) -> dict:
    cleaned = re.sub(r"```json|```", "", raw_text).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    return {
        "advice": raw_text,
        "urgency": "unknown",
        "recommended_specialist": None,
        "disclaimer": DEFAULT_DISCLAIMER,
    }


def _ocr_pdf(b64_data: str, custom_key: Optional[str] = None) -> str:
    # Mistral OCR endpoint specifically requires a Mistral key
    mistral_key = custom_key or os.getenv("MISTRAL_API_KEY") or get_llm_api_key(custom_key)
    if not mistral_key:
        raise ValueError("Mistral API key is required for PDF OCR processing. Please set MISTRAL_API_KEY in .env.")
    headers = {
        "Authorization": f"Bearer {mistral_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "mistral-ocr-latest",
        "document": {
            "type": "document_url",
            "document_url": f"data:application/pdf;base64,{b64_data}",
        },
    }
    resp = requests.post(MISTRAL_OCR_URL, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    pages = data.get("pages", [])
    return "\n".join(p.get("markdown", "") for p in pages).strip()


def run_consult_logic(
    symptoms: str = "",
    file_bytes: Optional[bytes] = None,
    content_type: str = "",
    api_key: Optional[str] = None,
    chat_history: Optional[List[Dict[str, Any]]] = None,
) -> dict:
    if not symptoms and not file_bytes:
        raise ValueError("Provide symptoms text, an uploaded report, or both.")

    # ------------------------------------------------------------------
    # 1. Fetch live PubMed citations (RAG grounding) from symptom text
    # ------------------------------------------------------------------
    pubmed_result = {"citations": [], "context_block": ""}
    if symptoms and symptoms.strip():
        try:
            pubmed_result = get_pubmed_citations(symptoms)
        except Exception as e:
            print("PUBMED ERROR:", e)
            pass  # graceful degradation — proceed without citations

    # ------------------------------------------------------------------
    # 2. Build text prompt
    # ------------------------------------------------------------------
    text_prompt = ""
    if symptoms:
        text_prompt += f"Patient-reported symptoms: {symptoms}\n\n"

    # Inject PubMed context block into prompt if available
    if pubmed_result["context_block"]:
        text_prompt += pubmed_result["context_block"] + "\n\n"

    image_data_uri = None

    if file_bytes:
        b64_data = base64.b64encode(file_bytes).decode("utf-8")
        ctype = (content_type or "").lower()

        if "pdf" in ctype:
            extracted_text = _ocr_pdf(b64_data, custom_key=api_key)
            text_prompt += f"Extracted report text:\n{extracted_text}\n\n"
        elif "image" in ctype or any(ext in ctype for ext in ["png", "jpg", "jpeg"]):
            image_data_uri = f"data:{ctype or 'image/jpeg'};base64,{b64_data}"
        else:
            raise ValueError("Unsupported file type. Please upload a PDF or an image (jpg/png).")

    text_prompt += "Respond with the JSON object described in your instructions."

    # ------------------------------------------------------------------
    # 3. Call LLM (DeepSeek / Mistral / OpenAI-compatible)
    # ------------------------------------------------------------------
    if image_data_uri:
        # Vision requests use vision model and if not explicitly configured, route to Mistral vision or custom URL
        model = get_vision_model()
        user_message = {
            "role": "user",
            "content": [
                {"type": "text", "text": text_prompt},
                {"type": "image_url", "image_url": image_data_uri},
            ],
        }
        chat_url = os.getenv("VISION_CHAT_URL") or (
            MISTRAL_CHAT_URL if "pixtral" in model.lower() else get_llm_chat_url()
        )
    else:
        model = get_text_model()
        user_message = {"role": "user", "content": text_prompt}
        chat_url = get_llm_chat_url()

    # Build messages list: system → prior history (last 10 turns) → current message
    history_messages = []
    if chat_history:
        for h in chat_history[-10:]:  # cap at last 10 turns to control token usage
            role = h.get("role", "user")
            content = h.get("content", "")
            if role in ("user", "assistant") and content:
                history_messages.append({"role": role, "content": str(content)})

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": MEDICAL_SYSTEM_PROMPT},
            *history_messages,
            user_message,
        ],
        "max_tokens": 1200,
    }

    headers = get_llm_headers(api_key)
    resp = requests.post(chat_url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()

    data = resp.json()
    raw_text = data["choices"][0]["message"]["content"]
    parsed = _extract_json(raw_text)

    return {
        "advice": parsed.get("advice", raw_text),
        "urgency": parsed.get("urgency", "unknown"),
        "recommended_specialist": parsed.get("recommended_specialist"),
        "disclaimer": parsed.get("disclaimer", DEFAULT_DISCLAIMER),
        # PubMed citations — new field (None-safe, frontend can ignore if absent)
        "citations": pubmed_result["citations"],
    }


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return r * 2 * atan2(sqrt(a), sqrt(1 - a))


def find_doctors_logic(location: str, specialty: Optional[str] = None, radius_km: float = 15.0) -> List[Dict[str, Any]]:
    # Read location API key from .env (checks LOCATION_API_KEY or LOCATIONIQ_API_KEY)
    api_key = os.getenv("LOCATION_API_KEY") or os.getenv("LOCATIONIQ_API_KEY")
    
    if not api_key:
        raise ValueError("LOCATION_API_KEY missing in environment variables (.env).")

    # 1. Geocode location string to Lat/Lon
    geocode_url = "https://us1.locationiq.com/v1/search"
    geo_params = {
        "key": api_key,
        "q": location,
        "format": "json",
        "limit": 1
    }
    
    geo_resp = requests.get(geocode_url, params=geo_params, headers=HTTP_HEADERS, timeout=15)
    if not geo_resp.ok or not geo_resp.json():
        raise ValueError("Could not geocode the provided location. Please try a different city or area.")

    geo_data = geo_resp.json()[0]
    lat, lon = float(geo_data["lat"]), float(geo_data["lon"])

    # 2. Query nearby hospitals, clinics, and doctors
    nearby_url = "https://us1.locationiq.com/v1/nearby"
    radius_meters = int(max(1.0, radius_km) * 1000)

    # Search for healthcare / hospital facilities
    nearby_params = {
        "key": api_key,
        "lat": lat,
        "lon": lon,
        "radius": radius_meters,
        "tag": "amenity:hospital,amenity:clinic,amenity:doctors,healthcare:*",
        "format": "json"
    }

    nearby_resp = requests.get(nearby_url, params=nearby_params, headers=HTTP_HEADERS, timeout=15)
    if not nearby_resp.ok:
        return []

    raw_places = nearby_resp.json()
    if not isinstance(raw_places, list):
        return []

    results = []
    search_term = specialty.strip().lower() if specialty else None

    for place in raw_places:
        name = place.get("display_name", "").split(",")[0].strip() or place.get("name")
        if not name:
            continue

        place_lat = float(place["lat"])
        place_lon = float(place["lon"])
        dist = _haversine_km(lat, lon, place_lat, place_lon)

        if dist > radius_km:
            continue

        # Soft specialty filter (if specialty passed, check name or tags)
        if search_term:
            full_meta = (name + " " + str(place.get("type", "")) + " " + str(place.get("class", ""))).lower()
            if search_term not in full_meta and "hospital" not in full_meta and "clinic" not in full_meta:
                continue

        results.append({
            "name": name,
            "address": place.get("display_name", "Address listed in LocationIQ"),
            "distance_km": round(dist, 2),
            "lat": place_lat,
            "lon": place_lon,
        })

    # Deduplicate & Sort by distance
    deduped = []
    seen = set()
    for item in results:
        if item["name"] not in seen:
            seen.add(item["name"])
            deduped.append(item)

    deduped.sort(key=lambda d: d["distance_km"])
    return deduped[:15]