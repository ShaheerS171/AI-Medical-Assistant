"""
frontend.py - Main Streamlit UI for AI Diagnostic Suite & Medical Assistant
Run with:
    streamlit run frontend.py
"""

import os
import requests
import streamlit as st
from PIL import Image

# Import Supabase Authentication Component
from Authentication.streamlit_auth import render_auth_ui

# Import Vision Models & Explainability Engines
from explainability.mistral_engine import MedicalExplainerAPI
from explainability.pdf_generator import MedicalReportPDFGenerator
from knee_model.src.inference import KneeOAPredictor
from knee_model.src.gradcam import run_gradcam
from tumor_model.src.inference import BrainTumorPredictor

# Import Chatbot Core Engine Logic
from chatbot.engine import run_consult_logic, find_doctors_logic

# Page Configuration
st.set_page_config(
    page_title="AI Medical Assistant | Clinical Support System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
    <style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #1E293B; margin-bottom: 0rem; }
    .sub-header { font-size: 1rem; color: #64748B; margin-bottom: 1.5rem; }
    .report-box { 
        background-color: #F8FAFC; 
        color: #0F172A; 
        padding: 1.5rem; 
        border-radius: 8px; 
        border: 1px solid #E2E8F0; 
        white-space: pre-wrap;
    }
    .citation-card {
        background: #F0F9FF;
        border-left: 4px solid #0EA5E9;
        border-radius: 6px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
        font-size: 0.85rem;
        color: #0F172A;
    }
    .urgency-high  { color: #DC2626; font-weight: 700; }
    .urgency-medium{ color: #D97706; font-weight: 700; }
    .urgency-low   { color: #16A34A; font-weight: 700; }
    </style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_knee_predictor():
    return KneeOAPredictor(
        checkpoint_path="knee_model/models/knee_ordinal_best.pth",
        metadata_path="knee_model/run_metadata.json"
    )


@st.cache_resource
def load_tumor_predictor():
    return BrainTumorPredictor(
        yolo_path="tumor_model/modelfiles/tumorbestyolo.pt",
        cls_path="tumor_model/modelfiles/MRIb3.pth"
    )


@st.cache_resource
def load_explainer_api():
    return MedicalExplainerAPI()


def main():
    # Render Supabase Authentication Gatekeeper in Sidebar
    is_authenticated, user = render_auth_ui(location="sidebar")

    if not is_authenticated:
        st.warning("🔒 Please sign in or register an account in the sidebar to access the AI Medical Assistant.")
        st.stop()

    st.sidebar.title("🏥 AI Diagnostic Suite")
    st.sidebar.caption("Select a diagnostic module or access patient triage services.")
    
    app_mode = st.sidebar.radio(
        "Navigation",
        [
            "🧠 Brain MRI (Tumor Detection)",
            "🦴 Knee X-Ray (Osteoarthritis)",
            "💬 Medical Consultation & Doctor Finder",
            "🔊 Ultrasound (Upcoming)"
        ]
    )

    st.sidebar.markdown("---")
    st.sidebar.info("💡 **Clinical Support:** System outputs are automated decision-support drafts and require review by a licensed healthcare professional.")

    if app_mode == "🧠 Brain MRI (Tumor Detection)":
        render_brain_mri_module()
    elif app_mode == "🦴 Knee X-Ray (Osteoarthritis)":
        render_knee_xray_module()
    elif app_mode == "💬 Medical Consultation & Doctor Finder":
        render_chatbot_module()
    elif app_mode == "🔊 Ultrasound (Upcoming)":
        render_ultrasound_module()


# ---------------------------------------------------------------------------
# Module 1: Brain MRI Scan Analysis
# ---------------------------------------------------------------------------
def render_brain_mri_module():
    st.markdown('<div class="main-header">Brain MRI Scan Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Classification, YOLO Segmentation Area Measurement, & LLM Draft Report</div>', unsafe_allow_html=True)

    col_input, col_form = st.columns([1, 1], gap="large")

    with col_input:
        st.subheader("1. Upload Imaging Scan")
        uploaded_file = st.file_uploader("Choose Brain MRI scan (JPG/PNG)...", type=["jpg", "png", "jpeg"], key="mri_upload")
        overlay_type = st.radio("Explainability Overlay", ["Grad-CAM Heatmap", "YOLO Bounding Box"], horizontal=True)

    with col_form:
        st.subheader("2. Patient Intake Form")
        with st.form("mri_patient_form"):
            p_name = st.text_input("Patient Full Name", "Jane Doe")
            p_id = st.text_input("Patient ID", "PAT-MRI-8841")
            col_a, col_b = st.columns(2)
            p_age = col_a.number_input("Age", 1, 120, 52)
            p_sex = col_b.selectbox("Biological Sex", ["Female", "Male", "Other"])
            p_history = st.text_area("Clinical Complaints & History", "Acute onset morning headaches associated with nausea and focal weakness.")
            submit_mri = st.form_submit_button("Run Analysis & Generate Report")

    if uploaded_file and submit_mri:
        image = Image.open(uploaded_file).convert("RGB")
        
        with st.spinner("Processing vision models & generating radiological report..."):
            tumor_predictor = load_tumor_predictor()
            explainer_api = load_explainer_api()

            results = tumor_predictor.predict(image)
            
            if overlay_type == "Grad-CAM Heatmap":
                overlay_img = tumor_predictor.generate_gradcam(
                    image, results["cls_tensor"], results["pred_idx"]
                )
            else:
                overlay_img = tumor_predictor.generate_detection_overlay(results["det_result"])

            patient_info = {"name": p_name, "id": p_id, "age": p_age, "sex": p_sex, "history": p_history}

            report_text = explainer_api.generate_tumor_report(
                predicted_class=results["predicted_class"],
                confidence=results["confidence"],
                patient_info=patient_info,
                area_mm2=results["tumor_area_mm2"],
                area_cm2=results["tumor_area_cm2"]
            )

        st.markdown("---")
        st.subheader("Vision Model Findings & Visualizations")
        col_img1, col_img2 = st.columns(2)
        col_img1.image(image, caption="Original MRI Input", use_container_width=True)
        col_img2.image(overlay_img, caption=f"Visual Analysis ({overlay_type})", use_container_width=True)

        m1, m2, m3 = st.columns(3)
        m1.metric("Predicted Category", results["predicted_class"].upper())
        m2.metric("Confidence Level", f"{results['confidence'] * 100:.1f}%")
        area_disp = f"{results['tumor_area_mm2']:.1f} mm²" if results['tumor_area_mm2'] else "N/A"
        m3.metric("Estimated Lesion Area", area_disp)

        st.markdown("---")
        st.subheader("3. Live Radiological Report Preview")
        st.markdown(f'<div class="report-box">{report_text}</div>', unsafe_allow_html=True)

        st.markdown("---")
        pdf_gen = MedicalReportPDFGenerator()
        metrics = {
            "Classification": results["predicted_class"].upper(),
            "Confidence": f"{results['confidence'] * 100:.1f}%",
            "Lesion Area": area_disp
        }
        pdf_bytes = pdf_gen.generate_pdf(
            patient_info=patient_info,
            report_text=report_text,
            original_img=image,
            overlay_img=overlay_img,
            metrics=metrics,
            scan_type="Brain MRI Scan"
        )

        st.download_button(
            label="📄 Download Medical PDF Report",
            data=pdf_bytes,
            file_name=f"Brain_MRI_Report_{p_id}.pdf",
            mime="application/pdf",
            use_container_width=True
        )


# ---------------------------------------------------------------------------
# Module 2: Knee Radiograph Analysis
# ---------------------------------------------------------------------------
def render_knee_xray_module():
    st.markdown('<div class="main-header">Knee Radiograph (X-Ray) Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Kellgren-Lawrence Ordinal Grading, Grad-CAM Heatmap, & Draft Report</div>', unsafe_allow_html=True)

    col_input, col_form = st.columns([1, 1], gap="large")

    with col_input:
        st.subheader("1. Upload Radiograph")
        uploaded_file = st.file_uploader("Choose Knee X-Ray scan (PNG/JPG)...", type=["png", "jpg", "jpeg"], key="knee_upload")

    with col_form:
        st.subheader("2. Patient Intake Form")
        with st.form("knee_patient_form"):
            p_name = st.text_input("Patient Full Name", "John Smith")
            p_id = st.text_input("Patient ID", "PAT-XRAY-4920")
            col_a, col_b = st.columns(2)
            p_age = col_a.number_input("Age", 1, 120, 64)
            p_sex = col_b.selectbox("Biological Sex", ["Male", "Female", "Other"])
            p_history = st.text_area("Clinical Complaints & History", "Worsening right knee stiffness during weight-bearing activities over 6 months.")
            submit_knee = st.form_submit_button("Run Analysis & Generate Report")

    if uploaded_file and submit_knee:
        image = Image.open(uploaded_file).convert("RGB")

        with st.spinner("Grading osteoarthritis severity & generating report..."):
            knee_predictor = load_knee_predictor()
            explainer_api = load_explainer_api()

            results = knee_predictor.predict(image)
            predicted_grade = results["predicted_grade"]

            overlay_img, _ = run_gradcam(knee_predictor.model, image, predicted_grade, knee_predictor.device)
            patient_info = {"name": p_name, "id": p_id, "age": p_age, "sex": p_sex, "history": p_history}

            report_text = explainer_api.generate_knee_report(
                predicted_grade=predicted_grade,
                confidence=results["confidence"],
                patient_info=patient_info
            )

        st.markdown("---")
        st.subheader("Vision Model Findings & Visualizations")
        col_img1, col_img2 = st.columns(2)
        col_img1.image(image, caption="Original X-Ray Input", use_container_width=True)
        col_img2.image(overlay_img, caption="Grad-CAM Cartilage Degeneration Overlay", use_container_width=True)

        m1, m2, m3 = st.columns(3)
        m1.metric("Severity Score", f"KL Grade {predicted_grade}")
        m2.metric("Grade Confidence", f"{results['confidence'] * 100:.1f}%")
        m3.metric("Calibration Status", "Calibrated" if results["calibrated"] else "Uncalibrated")

        st.markdown("---")
        st.subheader("3. Live Radiological Report Preview")
        st.markdown(f'<div class="report-box">{report_text}</div>', unsafe_allow_html=True)

        st.markdown("---")
        pdf_gen = MedicalReportPDFGenerator()
        metrics = {
            "Assessed Severity": f"KL Grade {predicted_grade}",
            "Confidence": f"{results['confidence'] * 100:.1f}%",
            "Calibration": "Active" if results["calibrated"] else "Default"
        }
        pdf_bytes = pdf_gen.generate_pdf(
            patient_info=patient_info,
            report_text=report_text,
            original_img=image,
            overlay_img=overlay_img,
            metrics=metrics,
            scan_type="Knee Radiograph (X-Ray)"
        )

        st.download_button(
            label="📄 Download Medical PDF Report",
            data=pdf_bytes,
            file_name=f"Knee_OA_Report_{p_id}.pdf",
            mime="application/pdf",
            use_container_width=True
        )


# ---------------------------------------------------------------------------
# Module 3: Chatbot & Doctor Finder
# ---------------------------------------------------------------------------
def render_chatbot_module():
    st.markdown('<div class="main-header">Medical Consultation & Doctor Locator</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">RAG-grounded symptom triage powered by Mistral AI + live PubMed citations</div>', unsafe_allow_html=True)

    tab_consult, tab_find = st.tabs(["💬 AI Medical Chat", "📍 Find Nearby Specialist"])

    # ------------------------------------------------------------------
    # Sub-Tab 1: Proper Chat Interface
    # ------------------------------------------------------------------
    with tab_consult:
        # Initialise session state
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []   # list of {role, content, meta}

        # ---- Render existing messages ----
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

                # Show citations attached to assistant messages
                citations = msg.get("citations", [])
                if citations:
                    with st.expander(f"📚 {len(citations)} source(s)", expanded=False):
                        for i, c in enumerate(citations, 1):
                            year_str = f" ({c['year']})" if c.get("year") else ""
                            journal_str = f" — *{c['journal']}*" if c.get("journal") else ""
                            authors_str = f"{c['authors']}" if c.get("authors") else ""
                            st.markdown(
                                f"""
                                <div class='citation-card'>
                                <b>[{i}]</b> {authors_str}{year_str}. 
                                <a href='{c['url']}' target='_blank'>{c['title']}</a>{journal_str}.
                                <br/><small>PMID: {c['pmid']}</small>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

        # ---- Optional file upload (above chat input) ----
        uploaded_doc = st.file_uploader(
            "📎 Attach a medical report (PDF / Image) — optional",
            type=["pdf", "png", "jpg", "jpeg"],
            key="chat_upload",
            label_visibility="collapsed",
        )
        if uploaded_doc:
            st.caption(f"📎 Attached: `{uploaded_doc.name}`")

        # ---- Chat input bar ----
        user_input = st.chat_input("Describe your symptoms (e.g. headache, fever for 3 days)...")

        if user_input or (uploaded_doc and st.session_state.get("_pending_upload")):
            prompt_text = user_input or "(no text — see attached file)"

            # Display user bubble immediately
            with st.chat_message("user"):
                st.markdown(prompt_text)
                if uploaded_doc:
                    st.caption(f"📎 {uploaded_doc.name}")

            st.session_state.chat_history.append({
                "role": "user",
                "content": prompt_text + (f"\n📎 *{uploaded_doc.name}*" if uploaded_doc else ""),
            })

            # Call backend
            with st.chat_message("assistant"):
                with st.spinner("Consulting medical knowledge base & PubMed..."):
                    try:
                        active_key = os.getenv("MISTRAL_API_KEY", "")
                        file_bytes = uploaded_doc.getvalue() if uploaded_doc else None
                        content_type = uploaded_doc.type if uploaded_doc else ""

                        # Pass prior turns so Mistral remembers the conversation
                        prior_history = [
                            {"role": m["role"], "content": m["content"]}
                            for m in st.session_state.chat_history
                        ]
                        res = run_consult_logic(
                            symptoms=user_input or "",
                            file_bytes=file_bytes,
                            content_type=content_type,
                            api_key=active_key,
                            chat_history=prior_history,
                        )

                        urgency = res.get("urgency", "unknown").lower()
                        badge_map = {"low": "🟢 LOW", "medium": "🟡 MEDIUM", "high": "🔴 HIGH"}
                        badge = badge_map.get(urgency, f"⚪ {urgency.upper()}")

                        advice = res.get("advice", "")
                        specialist = res.get("recommended_specialist")
                        disclaimer = res.get("disclaimer", "")
                        citations = res.get("citations", [])

                        # Build assistant message
                        response_md = f"**Urgency:** {badge}\n\n{advice}"
                        if specialist:
                            response_md += f"\n\n🩺 **Recommended Specialist:** {specialist}"
                        response_md += f"\n\n---\n⚠️ *{disclaimer}*"

                        st.markdown(response_md)

                        # Citations panel
                        if citations:
                            with st.expander(f"📚 {len(citations)} source(s)", expanded=False):
                                for i, c in enumerate(citations, 1):
                                    year_str = f" ({c['year']})" if c.get("year") else ""
                                    journal_str = f" — *{c['journal']}*" if c.get("journal") else ""
                                    authors_str = f"{c['authors']}" if c.get("authors") else ""
                                    st.markdown(
                                        f"""
                                        <div class='citation-card'>
                                        <b>[{i}]</b> {authors_str}{year_str}. 
                                        <a href='{c['url']}' target='_blank'>{c['title']}</a>{journal_str}.
                                        <br/><small>PMID: {c['pmid']}</small>
                                        </div>
                                        """,
                                        unsafe_allow_html=True,
                                    )

                        # Save to history
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": response_md,
                            "citations": citations,
                        })

                    except Exception as ex:
                        st.error(f"Consultation failed: {ex}")

        # Clear chat button
        if st.session_state.chat_history:
            if st.button("🗑️ Clear Chat History", key="clear_chat"):
                st.session_state.chat_history = []
                st.rerun()

    # ------------------------------------------------------------------
    # Sub-Tab 2: Doctor Finder (unchanged)
    # ------------------------------------------------------------------
    with tab_find:
        st.subheader("Search Nearby Healthcare Facilities")
        col_loc, col_spec = st.columns([2, 1])
        with col_loc:
            location = st.text_input("Current Location / City", placeholder="e.g. Rawalpindi, Pakistan")
        with col_spec:
            specialty = st.text_input("Specialist Search Term", placeholder="e.g. neurologist, orthopedist")

        radius_km = st.slider("Search Distance (Kilometers)", 5, 100, 15)

        if st.button("Locate Facilities", type="primary"):
            if not location:
                st.warning("Please enter a valid location.")
            else:
                with st.spinner(f"Locating facilities within {radius_km} km radius..."):
                    try:
                        results = find_doctors_logic(location, specialty, radius_km)
                        if not results:
                            st.info("No matching healthcare facilities found within the selected radius.")
                        else:
                            st.subheader(f"Found {len(results)} Facilities:")
                            for item in results:
                                st.markdown(f"**{item['name']}**")
                                if item.get("address"):
                                    st.write(f"📍 Location: {item['address']}")
                                if item.get("distance_km") is not None:
                                    st.write(f"📏 Distance: {item['distance_km']} km")
                                st.divider()
                    except Exception as ex:
                        st.error(f"Facility lookup failed: {ex}")


# ---------------------------------------------------------------------------
# Module 4: Ultrasound (Placeholders)
# ---------------------------------------------------------------------------
def render_ultrasound_module():
    st.markdown('<div class="main-header">Ultrasound Diagnostic Suite</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Module under active development</div>', unsafe_allow_html=True)
    st.info("🚧 **Upcoming Feature:** Reserved for automated abdominal and vascular ultrasound analysis modules.")


if __name__ == "__main__":
    main()