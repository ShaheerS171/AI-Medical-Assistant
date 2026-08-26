"""
app.py - Backend API for the Medical Assistant chatbot.

Two roles are exposed as separate endpoints:
  1. /consult       -> "Medical consultant" role. Accepts symptoms text and/or
                       an uploaded report (image or PDF), returns precautions,
                       an urgency level, and a recommended specialist (if any).
                       Uses the Mistral API (free tier) for text/vision, and
                       Mistral's OCR endpoint to read PDF reports.
  2. /find-doctors  -> "Doctor finder" role. Accepts a location (and optional
                       specialty) and returns nearby doctors/clinics using
                       OpenStreetMap (Nominatim + Overpass) - completely free,
                       no API key required.

Run with:
    uvicorn app:app --reload --port 8000

Requires a .env file (see .env.example) with:
    MISTRAL_API_KEY=...
"""

import base64
import json
import os
import re
from math import atan2, cos, radians, sin, sqrt
from typing import Optional

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()


def get_mistral_api_key(custom_key: Optional[str] = None):
    if custom_key and custom_key.strip():
        return custom_key.strip()
    key = os.getenv("MISTRAL_API_KEY")
    if not key or key.strip() in ("", "your_mistral_api_key_here"):
        try:
            import streamlit as st
            key = st.secrets.get("MISTRAL_API_KEY")
        except Exception:
            pass
    return key.strip() if key else None


MISTRAL_CHAT_URL = "https://api.mistral.ai/v1/chat/completions"
MISTRAL_OCR_URL = "https://api.mistral.ai/v1/ocr"

TEXT_MODEL = "mistral-small-latest"
VISION_MODEL = "pixtral-12b-2409"

app = FastAPI(title="Medical Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MEDICAL_SYSTEM_PROMPT = """You are a cautious medical information assistant embedded in a health app.
You are NOT a doctor and must never claim to give a diagnosis.

Given a patient's described symptoms and/or an uploaded medical report (image or PDF, the
latter already converted to text for you), do the following:
1. Summarize what you observe in plain, reassuring language.
2. Suggest general, safe precautions or self-care steps (nothing prescriptive like exact
   drug dosages).
3. Rate urgency as one of: "low", "medium", "high" ("high" = seek care immediately /
   emergency room).
4. Recommend a specialist type to see if relevant (e.g. "cardiologist", "dermatologist"),
   or null if a general physician / no visit is needed.
5. Always make clear this is not a diagnosis and a licensed physician should confirm.

Respond ONLY with a single JSON object and nothing else (no markdown fences, no preamble),
using exactly these keys:
{
  "advice": "<string, a few sentences>",
  "urgency": "<low|medium|high>",
  "recommended_specialist": "<string or null>",
  "disclaimer": "<string>"
}
"""

DEFAULT_DISCLAIMER = "This is not a medical diagnosis. Please consult a licensed physician."


class ConsultResponse(BaseModel):
    advice: str
    urgency: str
    recommended_specialist: Optional[str] = None
    disclaimer: str = DEFAULT_DISCLAIMER


class Doctor(BaseModel):
    name: str
    address: Optional[str] = None
    distance_km: Optional[float] = None
    lat: Optional[float] = None
    lon: Optional[float] = None


class DoctorSearchResponse(BaseModel):
    results: list[Doctor]


def _mistral_headers(custom_key: Optional[str] = None) -> dict:
    key = get_mistral_api_key(custom_key)
    if not key:
        raise ValueError(
            "Mistral API Key is missing. Please enter your free API key from https://console.mistral.ai/ in the sidebar or .env file."
        )
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def _extract_json(raw_text: str) -> dict:
    """Best-effort extraction of a JSON object from the model's reply."""
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
    """Use Mistral's OCR endpoint to extract text from a base64-encoded PDF."""
    payload = {
        "model": "mistral-ocr-latest",
        "document": {
            "type": "document_url",
            "document_url": f"data:application/pdf;base64,{b64_data}",
        },
    }
    resp = requests.post(MISTRAL_OCR_URL, headers=_mistral_headers(custom_key), json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    pages = data.get("pages", [])
    return "\n".join(p.get("markdown", "") for p in pages).strip()


def run_consult_logic(
    symptoms: str = "",
    file_bytes: Optional[bytes] = None,
    content_type: str = "",
    api_key: Optional[str] = None,
) -> dict:
    if not symptoms and not file_bytes:
        raise ValueError("Provide symptoms text, an uploaded report, or both.")

    text_prompt = ""
    if symptoms:
        text_prompt += f"Patient-reported symptoms: {symptoms}\n\n"

    image_data_uri = None

    if file_bytes:
        b64_data = base64.b64encode(file_bytes).decode("utf-8")
        ctype = (content_type or "").lower()

        if "pdf" in ctype:
            try:
                extracted_text = _ocr_pdf(b64_data, custom_key=api_key)
            except ValueError as ve:
                raise RuntimeError(str(ve))
            except requests.RequestException as e:
                detail = e.response.text if getattr(e, "response", None) is not None else str(e)
                if getattr(e, "response", None) and e.response.status_code in (401, 403):
                    raise RuntimeError("Invalid or unauthorized Mistral API Key. Please get a free API key at https://console.mistral.ai/")
                raise RuntimeError(f"OCR request failed: {detail}")
            text_prompt += f"Extracted report text:\n{extracted_text}\n\n"
        elif "image" in ctype or any(ext in ctype for ext in ["png", "jpg", "jpeg"]):
            image_data_uri = f"data:{ctype or 'image/jpeg'};base64,{b64_data}"
        else:
            raise ValueError("Unsupported file type. Please upload a PDF or an image (jpg/png).")

    text_prompt += "Respond with the JSON object described in your instructions."

    if image_data_uri:
        model = VISION_MODEL
        user_message = {
            "role": "user",
            "content": [
                {"type": "text", "text": text_prompt},
                {"type": "image_url", "image_url": image_data_uri},
            ],
        }
    else:
        model = TEXT_MODEL
        user_message = {"role": "user", "content": text_prompt}

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": MEDICAL_SYSTEM_PROMPT},
            user_message,
        ],
        "max_tokens": 1024,
    }

    try:
        headers = _mistral_headers(api_key)
        resp = requests.post(MISTRAL_CHAT_URL, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
    except ValueError as ve:
        raise RuntimeError(str(ve))
    except requests.RequestException as e:
        detail = e.response.text if getattr(e, "response", None) is not None else str(e)
        if (getattr(e, "response", None) and e.response.status_code in (401, 403)) or "Invalid API Key" in detail:
            raise RuntimeError(
                "Invalid or missing Mistral API Key. Please get a free API key from https://console.mistral.ai/ and enter it in the app sidebar or .env file."
            )
        raise RuntimeError(f"Mistral API error: {detail}")

    data = resp.json()
    raw_text = data["choices"][0]["message"]["content"]
    parsed = _extract_json(raw_text)

    return {
        "advice": parsed.get("advice", raw_text),
        "urgency": parsed.get("urgency", "unknown"),
        "recommended_specialist": parsed.get("recommended_specialist"),
        "disclaimer": parsed.get("disclaimer", DEFAULT_DISCLAIMER),
    }


@app.post("/consult", response_model=ConsultResponse)
async def consult(
    symptoms: str = Form(""),
    file: Optional[UploadFile] = File(None),
    api_key: Optional[str] = Form(None),
    x_api_key: Optional[str] = Header(None, alias="X-Mistral-Api-Key"),
):
    """Role 1: Medical consultant. Symptoms text and/or an uploaded report are optional
    individually, but at least one of them must be provided."""

    if not symptoms and not file:
        raise HTTPException(
            status_code=400,
            detail="Provide symptoms text, an uploaded report, or both.",
        )

    file_bytes = None
    content_type = ""
    if file is not None:
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        content_type = file.content_type or ""

    effective_key = api_key or x_api_key

    try:
        res = run_consult_logic(symptoms, file_bytes, content_type, api_key=effective_key)
        return ConsultResponse(**res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Role 2: Doctor finder (OpenStreetMap - free, no API key required)
# ---------------------------------------------------------------------------

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]
HTTP_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MedicalAssistantApp/1.0"}


def _geocode(location: str) -> Optional[tuple]:
    resp = requests.get(
        NOMINATIM_URL,
        params={"q": location, "format": "json", "limit": 1},
        headers=HTTP_HEADERS,
        timeout=15,
    )
    resp.raise_for_status()
    results = resp.json()
    if not results:
        return None
    return float(results[0]["lat"]), float(results[0]["lon"])


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return r * 2 * atan2(sqrt(a), sqrt(1 - a))


def _search_nominatim_doctors(
    location: str, specialty: Optional[str], center_lat: float, center_lon: float, radius_km: float = 15.0
) -> list[Doctor]:
    if specialty:
        search_terms = [
            specialty,
            f"{specialty} hospital",
            f"{specialty} clinic",
            "hospital",
            "clinic",
            "doctor",
        ]
    else:
        search_terms = ["hospital", "clinic", "doctor", "medical"]

    lat_delta = radius_km / 111.0
    lon_delta = radius_km / (111.0 * max(0.1, cos(radians(center_lat))))
    viewbox_str = f"{center_lon - lon_delta},{center_lat + lat_delta},{center_lon + lon_delta},{center_lat - lat_delta}"

    results = []
    seen_names = set()

    for term in search_terms:
        try:
            # First try bounded search around the viewbox
            items = []
            for bounded_val in [1, 0]:
                resp = requests.get(
                    NOMINATIM_URL,
                    params={
                        "q": f"{term} {location}",
                        "format": "json",
                        "limit": 15,
                        "addressdetails": 1,
                        "viewbox": viewbox_str,
                        "bounded": bounded_val,
                    },
                    headers=HTTP_HEADERS,
                    timeout=10,
                )
                if resp.ok and resp.json():
                    items = resp.json()
                    break

            for item in items:
                name = item.get("name") or item.get("display_name", "").split(",")[0]
                if not name or name in seen_names:
                    continue
                item_lat = float(item["lat"]) if "lat" in item else None
                item_lon = float(item["lon"]) if "lon" in item else None
                dist = (
                    _haversine_km(center_lat, center_lon, item_lat, item_lon)
                    if item_lat and item_lon
                    else None
                )
                # Strictly filter out any result outside the requested radius
                if dist is not None and dist > radius_km:
                    continue

                seen_names.add(name)
                results.append(
                    Doctor(
                        name=name,
                        address=item.get("display_name"),
                        distance_km=round(dist, 2) if dist is not None else None,
                        lat=item_lat,
                        lon=item_lon,
                    )
                )
            if len(results) >= 3 and term in [specialty, f"{specialty} hospital", f"{specialty} clinic"]:
                break
        except Exception:
            continue
    return results


@app.get("/find-doctors", response_model=DoctorSearchResponse)
def find_doctors(location: str, specialty: Optional[str] = None, radius_km: float = 15.0):
    """Role 2: Doctor finder. Takes a free-text location (city/address), an
    optional specialty, and an optional radius (default 15 km), returning nearby
    doctors/clinics via OpenStreetMap."""

    if not location:
        raise HTTPException(status_code=400, detail="Location is required.")

    try:
        coords = _geocode(location)
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Geocoding failed: {e}")

    if not coords:
        raise HTTPException(
            status_code=404,
            detail="Could not find that location. Try a more specific city or address.",
        )
    lat, lon = coords
    radius_meters = int(max(1.0, radius_km) * 1000)

    # Overpass QL query: search Nodes, Ways (buildings/polygons), and Relations (complexes)
    overpass_query = f"""
    [out:json][timeout:15];
    (
      nwr["amenity"~"doctors|clinic|hospital"](around:{radius_meters},{lat},{lon});
      nwr["healthcare"](around:{radius_meters},{lat},{lon});
      nwr["building"="hospital"](around:{radius_meters},{lat},{lon});
    );
    out center;
    """

    elements = []
    for endpoint in OVERPASS_ENDPOINTS:
        try:
            resp = requests.post(
                endpoint,
                data={"data": overpass_query},
                headers=HTTP_HEADERS,
                timeout=10,
            )
            if resp.ok:
                elements = resp.json().get("elements", [])
                if elements:
                    break
        except requests.RequestException:
            continue

    def to_doctor(el: dict) -> Optional[Doctor]:
        tags = el.get("tags", {})
        name = tags.get("name") or tags.get("name:en") or tags.get("operator")
        if not name:
            return None
        # Nodes have "lat"/"lon"; Ways and Relations return coordinates in "center" when using `out center;`
        el_lat = el.get("lat") or el.get("center", {}).get("lat")
        el_lon = el.get("lon") or el.get("center", {}).get("lon")
        distance = _haversine_km(lat, lon, el_lat, el_lon) if el_lat and el_lon else None
        if distance is not None and distance > radius_km:
            return None
        address_parts = [
            tags.get("addr:housenumber"),
            tags.get("addr:street"),
            tags.get("addr:suburb") or tags.get("addr:district"),
            tags.get("addr:city"),
        ]
        address = ", ".join(p for p in address_parts if p) or tags.get("address") or None
        return Doctor(
            name=name,
            address=address,
            distance_km=round(distance, 2) if distance is not None else None,
            lat=el_lat,
            lon=el_lon,
        )

    all_results = (
        [d for d in (to_doctor(el) for el in elements) if d is not None]
        if elements
        else []
    )

    if specialty and all_results:
        needle = specialty.lower()

        def matches(el: dict) -> bool:
            tags = el.get("tags", {})
            haystack = " ".join(
                str(v)
                for v in [
                    tags.get("name"),
                    tags.get("healthcare:speciality"),
                    tags.get("healthcare"),
                    tags.get("description"),
                ]
                if v
            ).lower()
            return needle in haystack

        filtered_elements = [el for el in elements if matches(el)]
        filtered_results = [
            d for d in (to_doctor(el) for el in filtered_elements) if d is not None
        ]
        results = filtered_results if filtered_results else all_results
    else:
        results = all_results

    # Fallback to Nominatim direct search if Overpass returns 0 results
    if not results:
        results = _search_nominatim_doctors(location, specialty, lat, lon, radius_km)

    # Strictly enforce radius filter on final aggregated list
    results = [
        d for d in results
        if d.distance_km is not None and d.distance_km <= radius_km
    ]

    # Deduplicate results by name
    deduped = []
    seen = set()
    for d in results:
        if d.name not in seen:
            seen.add(d.name)
            deduped.append(d)

    deduped.sort(key=lambda d: d.distance_km if d.distance_km is not None else 9999)
    return DoctorSearchResponse(results=deduped[:15])


@app.get("/health")
def health():
    return {"status": "ok"}
