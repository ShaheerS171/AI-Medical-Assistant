import io
import requests
import streamlit as st
from PIL import Image

st.set_page_config(page_title="AI Medical Assistant", page_icon="🏥", layout="wide")

API_URL = "http://localhost:8000"

st.title("🏥 Unified AI Medical Assistant Dashboard")

tab_knee, tab_brain = st.tabs(["🦴 Knee Osteoarthritis Grading", "🧠 Brain Tumor Analysis"])

# -----------------------------------------------------------------------------
# TAB 1: Knee Osteoarthritis Analysis
# -----------------------------------------------------------------------------
with tab_knee:
    st.header("Knee Osteoarthritis Severity Assessment")
    uploaded_knee = st.file_uploader("Upload Knee Radiograph (X-Ray)", type=["png", "jpg", "jpeg"], key="knee_upload")
    
    if uploaded_knee:
        col1, col2 = st.columns(2)
        image = Image.open(uploaded_knee).convert("RGB")
        col1.image(image, caption="Uploaded X-Ray", use_container_width=True)
        
        if col1.button("Run Knee Assessment & Report"):
            uploaded_knee.seek(0)
            file_bytes = uploaded_knee.read()
            files = {"file": (uploaded_knee.name, file_bytes, uploaded_knee.type)}
            
            with st.spinner("Evaluating Radiograph & Querying Explanation Engine..."):
                res = requests.post(f"{API_URL}/knee/predict", files=files)
                exp_res = requests.post(f"{API_URL}/knee/explain", files={"file": (uploaded_knee.name, file_bytes, uploaded_knee.type)})
                report_res = requests.post(f"{API_URL}/knee/explain-report", files={"file": (uploaded_knee.name, file_bytes, uploaded_knee.type)})
            
            if res.status_code == 200:
                data = res.json()
                col2.success(f"Predicted Severity Grade: KL Grade {data['predicted_grade']}")
                col2.metric("Confidence Score", f"{data['confidence']*100:.1f}%")
                
                # Render probability distribution breakdown
                st.write("**Grade Probabilities:**")
                for idx, prob in enumerate(data['grade_probabilities']):
                    st.progress(prob, text=f"Grade {idx}: {prob*100:.1f}%")
                
                if exp_res.status_code == 200:
                    overlay_img = Image.open(io.BytesIO(exp_res.content))
                    col2.image(overlay_img, caption="Grad-CAM Attention Map", use_container_width=True)

            if report_res.status_code == 200:
                st.markdown("---")
                st.markdown("### 📋 Automated Clinical Assessment Report")
                st.info(report_res.json()["report"])

# -----------------------------------------------------------------------------
# TAB 2: Brain Tumor Detection & Area Measurement
# -----------------------------------------------------------------------------
with tab_brain:
    st.header("Brain Scan Classification & YOLO Segmentation")
    uploaded_brain = st.file_uploader("Upload Brain MRI Scan", type=["png", "jpg", "jpeg"], key="brain_upload")
    
    if uploaded_brain:
        col1, col2, col3 = st.columns(3)
        image = Image.open(uploaded_brain).convert("RGB")
        col1.image(image, caption="Uploaded Brain MRI", use_container_width=True)
        
        if st.button("Run Brain MRI Analysis & Report"):
            uploaded_brain.seek(0)
            file_bytes = uploaded_brain.read()
            files = {"file": (uploaded_brain.name, file_bytes, uploaded_brain.type)}
            
            with st.spinner("Processing MRI Scan & Querying Explanation Engine..."):
                res = requests.post(f"{API_URL}/brain/predict", files=files)
                cam_res = requests.post(f"{API_URL}/brain/explain-cam", files={"file": (uploaded_brain.name, file_bytes, uploaded_brain.type)})
                det_res = requests.post(f"{API_URL}/brain/explain-detection", files={"file": (uploaded_brain.name, file_bytes, uploaded_brain.type)})
                report_res = requests.post(f"{API_URL}/brain/explain-report", files={"file": (uploaded_brain.name, file_bytes, uploaded_brain.type)})
            
            if res.status_code == 200:
                data = res.json()
                st.subheader(f"Classification: {data['predicted_class'].upper()} (Confidence: {data['confidence']*100:.1f}%)")
                
                if data['tumor_area_mm2'] is not None:
                    st.warning(
                        f"**Estimated Tumor Physical Size:** "
                        f"{data['tumor_area_mm2']:.1f} mm² ({data['tumor_area_cm2']:.2f} cm² / {data['tumor_area_pixels']:.0f} px²)"
                    )
                else:
                    st.info("No localized tumor bounding box detected by YOLO model.")
                
                if cam_res.status_code == 200:
                    col2.image(Image.open(io.BytesIO(cam_res.content)), caption="Classifier Grad-CAM Focus", use_container_width=True)
                if det_res.status_code == 200:
                    col3.image(Image.open(io.BytesIO(det_res.content)), caption="YOLO Bounding Box Localization", use_container_width=True)

            if report_res.status_code == 200:
                st.markdown("---")
                st.markdown("### 📋 Automated Clinical Assessment Report")
                st.info(report_res.json()["report"])