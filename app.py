"""
====================================================================================================
                                    VITISCAN PRO - Streamlit UI
              Web interface for grape leaf disease diagnosis and treatment planning
====================================================================================================
"""

#                                         LIBRARIES IMPORT
# ================================================================================================

import os
import json
import logging
from datetime import datetime

import requests
import streamlit as st
import folium
from PIL import Image, ExifTags
from streamlit_folium import st_folium
from dotenv import load_dotenv


#                                         CONFIGURATION
# ================================================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

API_DIAGNO   = os.getenv("API_DIAGNO",   "https://localhost:4000").replace('"', '')
API_SOLUTIONS = os.getenv("API_SOLUTIONS", "https://localhost:9000").replace('"', '')
MOCK  = int(os.getenv("MOCK",  "0"))
DEBUG = int(os.getenv("DEBUG", "0"))

OPTIONS_MODE = {
    "conventional": "Conventional",
    "organic":      "Organic"
}
OPTIONS_SEVERITY = {
    "low":      "Low",
    "moderate": "Moderate",
    "high":     "High"
}

MAP_STYLES = ["OpenStreetMap", "CartoDB Positron", "CartoDB Voyager"]

NOW = datetime.now().strftime("%Y-%m-%d")

SESSION_VARS       = ['payload', 'solutions', 'diagnostic', 'img_date', 'img_long', 'img_lat', 'previous_file']
SESSION_CONTAINERS = ['vitiscan_form', 'container_diagno', 'container_solutions']


#                                         HELPER FUNCTIONS
# ================================================================================================

def reset_session():
    """Resets session variables and containers when a new file is uploaded."""
    for key in SESSION_VARS + SESSION_CONTAINERS:
        if st.session_state.get(key):
            del st.session_state[key]


def get_exif_data(image) -> tuple:
    """
    Extracts GPS coordinates and capture date from image EXIF metadata.

    Args:
        image: Uploaded image file

    Returns:
        Tuple (longitude, latitude, date_string)
    """
    lon, lat, date = 0.0, 0.0, NOW
    try:
        img  = Image.open(image)
        exif = img._getexif()
        if exif:
            for tag, value in exif.items():
                decoded = ExifTags.TAGS.get(tag, tag)
                if decoded == "GPSInfo":
                    deg, min_, sec = value[2]
                    lat = int(deg) + int(min_) / 60 + int(sec) / 3600
                    deg, min_, sec = value[4]
                    lon = int(deg) + int(min_) / 60 + int(sec) / 3600
                elif decoded == "DateTimeOriginal":
                    try:
                        dt   = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                        date = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        pass
    except Exception:
        pass
    return (lon, lat, date)


def call_api_diagnostic(uploaded_file) -> dict:
    """
    Calls the Diagnostic API to classify the uploaded leaf image.

    Args:
        uploaded_file: Streamlit uploaded file object

    Returns:
        Dictionary with predictions and model version
    """
    if MOCK:
        return {
            'predictions': [
                {'disease': 'anthracnose', 'confidence': 0.75},
                {'disease': 'healthy',     'confidence': 0.14}
            ],
            'model_version': 'resnet18_finetuning_v1'
        }

    files    = {"file": uploaded_file}
    response = requests.post(
        f"{API_DIAGNO}/diagno",
        files=files
    )
    if response.status_code != 200:
        logger.error(f"Diagnostic API error {response.status_code}: {response.text}")
        return {'error': response.text, 'status_code': response.status_code}
    return response.json()


def call_api_solutions(payload: dict, debug: bool = False) -> dict:
    """
    Calls the Treatment Plan API to get recommendations based on the diagnosis.

    Args:
        payload: Dictionary with diagnosis info (disease, severity, area, etc.)
        debug: If True, includes raw LLM output in response

    Returns:
        Dictionary with treatment plan and recommendations
    """
    if MOCK:
        return {
            "data": {
                "cnn_label": "healthy",
                "treatment_plan": {"dose_l_ha": 200, "area_m2": 0.5}
            }
        }

    response = requests.post(
        f"{API_SOLUTIONS}/solutions",
        params={'debug': str(debug)},
        json=payload,
        timeout=60
    )
    if response.status_code != 200:
        logger.error(f"Solutions API error {response.status_code}: {response.text}")
        return {}
    return response.json()


@st.cache_data
def get_diseases() -> tuple:
    """
    Retrieves the disease label dictionary from the Diagnostic API.

    Returns:
        Tuple (dataset_name, diseases_dict)
    """
    if MOCK:
        return ("inrae", {
            "colomerus_vitis":             "Erinose",
            "elsinoe_ampelina":            "Anthracnose",
            "erysiphe_necator":            "Oidium",
            "guignardia_bidwellii":        "Black rot",
            "healthy":                     "Healthy",      
            "phaeomoniella_chlamydospora": "Esca",       
            "plasmopara_viticola":         "Mildiou"        
        })

    try:
        response = requests.get(
            f"{API_DIAGNO}/diseases",
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        return (data['dataset_name'], dict(data['diseases']))
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to retrieve diseases from API: {e}")
        return ("unknown", {})


#                                         MAIN APPLICATION
# ================================================================================================

def main():

    logger.info(f"API_DIAGNO={API_DIAGNO} | API_SOLUTIONS={API_SOLUTIONS} | MOCK={MOCK} | DEBUG={DEBUG}")

    # Page config must be called first
    st.set_page_config(page_title="VitiScan Pro", page_icon="🍇")

    # Custom background color
    st.markdown("""
        <style>
        .stApp { background-color: #F5F7F4; }
        </style>
    """, unsafe_allow_html=True)

    # Initialize all session state variables
    for key in SESSION_VARS:
        if key not in st.session_state:
            st.session_state[key] = None

    # Load disease labels from API
    DATASET_NAME, DISEASE_LABELS = get_diseases()
    logger.info(f"Dataset: {DATASET_NAME} | Diseases: {list(DISEASE_LABELS.keys())}")

    st.title("🍇 VitiScan Pro — Vine Disease Diagnosis")

    if DEBUG:
        st.sidebar.write("DEBUG — Session State:", st.session_state)

    # ---- COLUMNS: Upload + Map ----
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Leaf Diagnosis")

        uploaded_file = st.file_uploader(
            label="Upload a grape leaf photo",
            type=["jpg", "jpeg", "png", "webp"],
            on_change=reset_session
        )

        # Update previous_file and display image when file is uploaded
        if uploaded_file:
            st.session_state.previous_file = uploaded_file
            st.image(uploaded_file, caption="Uploaded image", width=300)

        submit = st.button(
            label="Run diagnosis",
            disabled=(uploaded_file is None),
            type="primary"
        )

        if submit and uploaded_file:
            with st.spinner("Running diagnosis..."):
                diagnostic = call_api_diagnostic(uploaded_file)
                st.session_state.diagnostic = diagnostic
                st.success("Diagnosis complete.")
                if DEBUG:
                    with st.expander("DEBUG — Diagnostic API response"):
                        st.code(json.dumps(diagnostic, indent=2), language="json")

    with col2:
        st.subheader("Parcel Map")
        if uploaded_file:
            lon, lat, date = get_exif_data(uploaded_file)
            st.session_state.img_long = lon
            st.session_state.img_lat  = lat
            st.session_state.img_date = date

            if lon and lat:
                m = folium.Map(location=[lat, lon], zoom_start=12, tiles=MAP_STYLES[0])
                folium.Marker([lat, lon], popup="Parcel").add_to(m)
                st_folium(m, height=400)
            else:
                st.warning("No GPS data found in this image.")

    # ---- DIAGNOSIS RESULTS ----
    if st.session_state.get("diagnostic"):
        diagno = st.session_state.diagnostic
        with st.container():
            if 'error' in diagno:
                st.error(f"API Error {diagno.get('status_code')}: {diagno.get('error')}")
            elif 'predictions' in diagno:
                best = diagno['predictions'][0]
                st.write("### Diagnosis result")
                c1, c2 = st.columns(2)
                with c1:
                    disease_key   = best.get('disease', 'N/A')
                    disease_label = DISEASE_LABELS.get(disease_key, disease_key)
                    st.metric("Detected disease", disease_label)
                with c2:
                    confidence = best.get('confidence', 0)
                    st.metric("Confidence score", f"{confidence * 100:.1f}%")

        # ---- TREATMENT PLAN FORM ----
        with st.form(key="vitiscan_form"):
            st.write("### Treatment Plan")

            mode = st.selectbox(
                "Farming mode",
                options=OPTIONS_MODE.keys(),
                format_func=lambda x: OPTIONS_MODE[x],
                index=1
            )
            severity = st.selectbox(
                "Severity",
                options=OPTIONS_SEVERITY.keys(),
                format_func=lambda x: OPTIONS_SEVERITY[x],
                index=0
            )
            area_ha = st.slider("Area (ha)", min_value=0.1, max_value=5.0, value=0.5, step=0.1)

            # Hidden fields — visible only in DEBUG mode
            placeholder = st.empty()
            with placeholder.container():
                cnn_label = st.text_input(
                    "cnn_label",
                    diagno['predictions'][0].get("disease", "healthy") if 'predictions' in diagno else "N/A",
                    disabled=True
                )
                date_iso = st.text_input(
                    "date_iso",
                    st.session_state.img_date or NOW,
                    disabled=True
                )
                debug = st.checkbox(
                    "Include raw LLM output (debug)",
                    disabled=True,
                    value=(DEBUG == 1)
                )
            if not DEBUG:
                placeholder.empty()

            submitted = st.form_submit_button("Request treatment plan", type="primary")

            payload = {
                "cnn_label": cnn_label,
                "mode":      mode,
                "severity":  severity,
                "area_m2":   area_ha * 10000,
                "date_iso":  date_iso,
                "location":  f"{st.session_state.img_lat},{st.session_state.img_long}"
            }
            st.session_state.payload = payload

            if submitted and st.session_state.get("payload"):
                if DEBUG:
                    with st.expander("DEBUG — Request payload"):
                        st.code(json.dumps(payload, indent=2), language="json")
                with st.spinner("Computing treatment plan..."):
                    try:
                        response = call_api_solutions(payload, debug)
                        st.session_state.solutions = response
                        st.success("Treatment plan ready.")
                    except Exception as e:
                        st.error(f"Failed to compute treatment plan: {e}")

    # ---- TREATMENT RESULTS ----
    if st.session_state.get("solutions"):
        with st.container():
            data = st.session_state.solutions.get("data", {})
            if not data:
                st.error("No treatment data received.")
            else:
                with st.expander("Summary", expanded=True):
                    st.markdown(f"**Detected disease** : {DISEASE_LABELS.get(data.get('cnn_label', 'N/A'), 'N/A')}")
                    st.markdown(f"**Severity** : {data.get('severity', '')}")
                    st.markdown(f"**Mode** : {data.get('mode', '')}")
                    st.markdown(f"**Season** : {data.get('season', '')}")

                with st.expander("Treatment actions", expanded=True):
                    tp = data.get("treatment_plan", {})
                    if tp:
                        for item in tp.get("treatment_product", []):
                            key, val = item.split(":", 1)
                            st.markdown(f"- **{key.strip()}** : {val.strip()}")
                        if tp.get("dose_l_ha"):
                            st.markdown(f"- **Dose per ha** : {tp['dose_l_ha']} L/ha")
                            st.markdown(f"- **Area** : {tp.get('area_m2')} m²")
                            st.markdown(f"- **Estimated total volume** : {tp.get('volume_bouillie_l_ha')} L")
                    for action in data.get("treatment_actions", []):
                        if action:
                            st.markdown(f"- {action}")

                with st.expander("Preventive measures", expanded=True):
                    for action in data.get("preventive_actions", []):
                        if action:
                            st.markdown(f"- {action}")

                with st.expander("Warnings", expanded=True):
                    for w in data.get("warnings", []):
                        if w:
                            st.markdown(f"- {w}")

                if DEBUG:
                    with st.expander("DEBUG — Raw LLM output", expanded=False):
                        if data.get("raw_llm_output"):
                            st.write(data["raw_llm_output"])


if __name__ == "__main__":
    main()