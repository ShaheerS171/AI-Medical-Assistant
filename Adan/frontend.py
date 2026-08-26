"""
frontend.py - Streamlit frontend for the Medical Assistant chatbot.
"""

import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000")


def _direct_consult(symptoms_text, file_obj):
    from app import run_consult_logic
    file_bytes = file_obj.getvalue() if file_obj else None
    content_type = file_obj.type if file_obj else ""
    return run_consult_logic(symptoms_text, file_bytes, content_type)


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

    if st.button("Get Consultation", type="primary"):
        if not symptoms and not uploaded_file:
            st.warning("Please describe your symptoms or upload a report first.")
        else:
            with st.spinner("Analyzing..."):
                result = None
                err_msg = None
                try:
                    data = {"symptoms": symptoms}
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
                        f"{API_URL}/consult", data=data, files=files, timeout=60
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

                # Direct python invocation fallback for Streamlit Cloud deployment
                if result is None and err_msg is None:
                    try:
                        result = _direct_consult(symptoms, uploaded_file)
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
