"""
frontend.py - Streamlit frontend for the Medical Assistant chatbot.
"""

import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000")


def _direct_consult(symptoms_text, file_obj, api_key=None):
    from app import run_consult_logic
    file_bytes = file_obj.getvalue() if file_obj else None
    content_type = file_obj.type if file_obj else ""
    return run_consult_logic(symptoms_text, file_bytes, content_type, api_key=api_key)


def _direct_find_doctors(loc, spec, radius=15.0):
    from app import find_doctors
    res = find_doctors(loc, spec, radius_km=radius)
    return [
        {
            "name": d.name,
            "address": d.address,
            "distance_km": d.distance_km,
            "lat": d.lat,
            "lon": d.lon,
        }
        for d in res.results
    ]


st.set_page_config(page_title="Medical Assistant", page_icon="🩺", layout="centered")

# ---------------------------------------------------------------------------
# Sidebar Settings
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Settings")
    st.subheader("API Configuration")
    
    default_key = os.getenv("MISTRAL_API_KEY", "")
    if default_key == "your_mistral_api_key_here":
        default_key = ""
        
    current_key = st.session_state.get("user_mistral_api_key", default_key)
    
    user_key_input = st.text_input(
        "Mistral API Key",
        value=current_key,
        type="password",
        help="Enter your Mistral API key here. Required for AI consultations."
    )
    
    if user_key_input != current_key:
        st.session_state["user_mistral_api_key"] = user_key_input.strip()
        st.success("API Key updated!")
    
    st.markdown("---")
    st.markdown(
        "🔑 **How to get a FREE API Key:**\n"
        "1. Visit [console.mistral.ai](https://console.mistral.ai/)\n"
        "2. Create a free account or log in\n"
        "3. Navigate to **API Keys** → **Create new key**\n"
        "4. Copy and paste your key above!"
    )

st.title("🩺 Medical Assistant")
st.caption(
    "This tool provides general information only and is not a substitute for "
    "professional medical advice, diagnosis, or treatment."
)

tab_consult, tab_find = st.tabs(["💬 Consult", "📍 Find a Doctor"])

# ---------------------------------------------------------------------------
# Role 1: Medical consultant
# ---------------------------------------------------------------------------
with tab_consult:
    st.subheader("Describe your symptoms or upload a report")
    st.write(
        "You can type your symptoms, upload a report/scan, or both. "
        "If you'd rather just consult directly, leave the upload empty."
    )

    symptoms = st.text_area(
        "Describe your symptoms (optional if uploading a report)",
        placeholder="e.g. I've had a mild fever and sore throat for 2 days...",
        height=120,
    )

    uploaded_file = st.file_uploader(
        "Upload a report or scan (optional)",
        type=["pdf", "png", "jpg", "jpeg"],
        help="PDF lab reports or image scans (X-ray, photo of a rash, etc.) are supported.",
    )

    active_api_key = st.session_state.get("user_mistral_api_key") or os.getenv("MISTRAL_API_KEY", "")
    if active_api_key == "your_mistral_api_key_here":
        active_api_key = ""

    if st.button("Get Consultation", type="primary"):
        if not symptoms and not uploaded_file:
            st.warning("Please describe your symptoms or upload a report first.")
        else:
            with st.spinner("Analyzing..."):
                result = None
                err_msg = None
                
                # Attempt 1: HTTP API request to backend
                try:
                    data = {"symptoms": symptoms}
                    if active_api_key:
                        data["api_key"] = active_api_key
                    
                    headers = {}
                    if active_api_key:
                        headers["X-Mistral-Api-Key"] = active_api_key

                    files = None
                    if uploaded_file is not None:
                        files = {
                            "file": (
                                uploaded_file.name,
                                uploaded_file.getvalue(),
                                uploaded_file.type,
                            )
                        }
                    resp = requests.post(
                        f"{API_URL}/consult", data=data, files=files, headers=headers, timeout=60
                    )
                    if resp.ok:
                        result = resp.json()
                    else:
                        try:
                            err_msg = resp.json().get("detail", resp.text)
                        except Exception:
                            err_msg = resp.text
                except Exception:
                    pass

                # Attempt 2: Direct python invocation fallback for Streamlit Cloud deployment or offline backend
                if result is None and (err_msg is None or "Connection" in str(err_msg) or "refused" in str(err_msg)):
                    try:
                        result = _direct_consult(symptoms, uploaded_file, api_key=active_api_key)
                        err_msg = None
                    except Exception as ex:
                        err_msg = str(ex)

            if result is not None:
                urgency = result.get("urgency", "unknown").lower()
                urgency_color = {"low": "green", "medium": "orange", "high": "red"}.get(
                    urgency, "gray"
                )

                st.markdown(f"**Urgency:** :{urgency_color}[{urgency.upper()}]")
                st.markdown("**Advice:**")
                st.write(result.get("advice", ""))

                if result.get("recommended_specialist"):
                    st.markdown(
                        f"**Recommended specialist:** {result['recommended_specialist']}"
                    )
                    st.info(
                        "You can look up nearby specialists in the "
                        "'Find a Doctor' tab."
                    )

                st.caption(f"⚠️ {result.get('disclaimer', 'This is not a medical diagnosis.')}")
            else:
                st.error(f"Something went wrong: {err_msg or 'Could not process request.'}")
                
                is_key_error = (
                    not active_api_key
                    or "Invalid API Key" in str(err_msg)
                    or "Invalid" in str(err_msg)
                    or "missing" in str(err_msg)
                    or "unauthorized" in str(err_msg)
                    or "401" in str(err_msg)
                )
                
                if is_key_error:
                    st.warning(
                        "🔑 **Mistral API Key issue detected!**\n\n"
                        "To fix this error:\n"
                        "1. Get a free API key at [console.mistral.ai](https://console.mistral.ai/)\n"
                        "2. Enter your API key in the field below and click **Save Key & Retry**:"
                    )
                    new_inline_key = st.text_input(
                        "Enter valid Mistral API key:",
                        type="password",
                        key="inline_key_box"
                    )
                    if st.button("Save Key & Retry", type="primary"):
                        if new_inline_key.strip():
                            st.session_state["user_mistral_api_key"] = new_inline_key.strip()
                            st.success("API Key saved! Processing your request now...")
                            st.rerun()

# ---------------------------------------------------------------------------
# Role 2: Doctor finder
# ---------------------------------------------------------------------------
with tab_find:
    st.subheader("Find nearby doctors")

    location = st.text_input(
        "Your location", placeholder="e.g. Rawalpindi, Pakistan or a street address"
    )
    specialty = st.text_input(
        "Specialist type (optional)", placeholder="e.g. cardiologist, dermatologist"
    )
    radius_km = st.slider(
        "Maximum distance (km)", min_value=5, max_value=100, value=15, step=5
    )

    if st.button("Search", type="primary"):
        if not location:
            st.warning("Please enter your location.")
        else:
            with st.spinner(f"Searching nearby doctors within {radius_km} km..."):
                results = None
                err_msg = None
                try:
                    resp = requests.get(
                        f"{API_URL}/find-doctors",
                        params={
                            "location": location,
                            "specialty": specialty,
                            "radius_km": radius_km,
                        },
                        timeout=30,
                    )
                    if resp.ok:
                        results = resp.json().get("results", [])
                    else:
                        try:
                            err_msg = resp.json().get("detail", resp.text)
                        except Exception:
                            err_msg = resp.text
                except Exception:
                    pass

                # Direct python invocation fallback for Streamlit Cloud deployment
                if results is None and err_msg is None:
                    try:
                        results = _direct_find_doctors(location, specialty, radius=radius_km)
                    except Exception as ex:
                        err_msg = str(ex)

            if results is not None:
                if not results:
                    st.info(
                        f"No doctors or specialists found within {radius_km} km. "
                        "Try increasing the maximum distance radius or searching without a specialist filter."
                    )
                for r in results:
                    st.markdown(f"**{r['name']}**")
                    if r.get("address"):
                        st.write(f"📍 {r['address']}")
                    if r.get("distance_km") is not None:
                        st.write(f"📏 Distance: {r['distance_km']} km")
                    st.divider()
            else:
                st.error(f"Something went wrong: {err_msg or 'Could not fetch doctors.'}")

