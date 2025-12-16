import os
import json
import streamlit as st
import requests
import folium
from PIL import Image, ExifTags
from streamlit_folium import st_folium
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# API URL (à adapter selon déploiement)
API_DIAGNO = os.getenv("API_DIAGNO", "https://localhost:4000").replace('"','')
API_SOLUTIONS = os.getenv("API_SOLUTIONS", "https://localhost:9000").replace('"','')

# var pour mock et debug
MOCK = int(os.getenv("MOCK", "0"))
DEBUG = int(os.getenv("DEBUG", "0"))

# TODO la traduction devrait etre faite dans l'API solutions
DISEASE_TRANSLATION = {
    "anthracnose": "Anthracnose",
    "brown_spot": "Tâche brune",
    "downy_mildew": "Mildiou",
    "mites": "Acariens",
    "normal": "Pas de maladie",
    "powdery_mildew": "Oïdium",
    "shot_hole": "Coryneum",
    "N/A":"N/A"
}
OPTIONS_MODE = ["conventionnel", "bio"]
OPTIONS_SEVERITY = ["faible", "modérée", "forte"]

# styles de carte pour Folium
MAP_STYLE = ["OpenStreetMap", "CartoDB Positron", "CartoDB Voyager"]

HEADERS = {
#    'Content-Type' : 'application/json',
    'Accept-Encoding':'gzip, deflate, br, zstd',
    'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0'
}
NOW = datetime.now().strftime("%Y-%m-%d")

SESSION_VARS = ['payload', 'solutions', 'diagnostic', 'img_date', 'img_long', 'img_lat', 'previous_file']
SESSION_CONTAINERS = ['vitiscan_form', 'container_diagno', 'container_solutions']

def reset_form_and_containers():
    '''Reinit session vars, form and containers when uploaded file change'''
    for key in SESSION_VARS:
        if st.session_state.get(key): del st.session_state[key]
    for key in SESSION_CONTAINERS:
        if st.session_state.get(key): del st.session_state[key]
    st.rerun()

def get_exif_data(image):
    """Extrait les données EXIF (latitude, longitude) de l'image."""
    try:
        lon,lat,date = 0.0, 0.0, NOW
        img = Image.open(image)
        exif = img._getexif()
        if exif:
            for tag, value in exif.items():
                decoded = ExifTags.TAGS.get(tag, tag)
                if decoded == "GPSInfo":
                    degre,minute,seconde = value[2]
                    lat = int(degre) + int(minute)/60 + int(seconde)/3600
                    degre,minute,seconde = value[4]
                    lon = int(degre) + int(minute)/60 + int(seconde)/3600
                elif decoded == "DateTimeOriginal":
                    try:
                        dt = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                        date = dt.strftime("%Y-%m-%d %H:%M:%S")
                        print("EXIF date = ", date)
                    except:
                        # error ou date non renseignée
                        pass
        #else:
        #    st.write("Pas de données de localisation dans l'image")
    except Exception as e:
        #st.error(f"Erreur EXIF: {e}")
        pass
    return (lon,lat,date)

def call_api_diagnostic(uploaded_file):
    """Appel API pour obtenir un diagnostic."""
    if MOCK == 1:
        # ATTENTION ici en mock dictionnaire
        diagnostic = {
            'predictions' : [
                {'disease': 'anthracnose', 'confidence': 0.75 },
                {'disease': 'normal', 'confidence': 0.14 }],
            'model_version': 'Resnet34_30ep_v1'
        }
        return diagnostic
    else:
        # ATTENTION ici l'API renvoie un dictionnaire seulement
        files = {"file": uploaded_file }
        response = requests.post(f"{API_DIAGNO}/diagno", files=files, headers=HEADERS, verify=False)
        if response.status_code != 200:
            print(f'Error: {response.status_code}')
            print(response.text)
            return {'error': response.text, 'status_code': response.status_code }
        else:
            return response.json()

def call_api_solutions(diagno_payload):
    """Appel API pour obtenir les traitements."""
    if MOCK == 1:
        treatment = { "data" : { "cnn_label": "normal", "treatment_plan": {"dose_l_ha": 200, "area_m2": 0.5} } }
        return treatment
    else:
        response = requests.post(f"{API_SOLUTIONS}/solutions",
                                 json=diagno_payload,
                                 headers=HEADERS,
                                 timeout=60,
                                 verify=False)
        if response.status_code != 200:
            print(f'Error: {response.status_code}')
            print(response.text)
        else:
            return response.json()
        
##############################################################
#----------------------- MAIN -------------------------------
##############################################################
def main():
    # la modif du backgroundColor ne fonctionne pas dans .streamlit/config.toml
    # il faut forcer par CSS
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #F5F7F4;  /* Light beige background */
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.set_page_config(page_title="VitiScan Pro", page_icon="🍇")
    
    st.title("VitiScan Pro: Diagnostic & Gestion des Vignes")

    col1, col2 = st.columns(2)

    # initialisation des variables de session
    for key in SESSION_VARS:
        if key not in st.session_state:
            st.session_state[key] = None

    if DEBUG:
        st.sidebar.write("DEBUG Session State:", st.session_state)

    with col1:
        st.subheader("Diagnostic Foliaire")

        uploaded_file = st.file_uploader(
                label="Téléchargez une photo de feuille de vigne",
                type=["jpg", "png","jpeg"],
                on_change=reset_form_and_containers,
            )

        if uploaded_file:
            st.image(uploaded_file, caption="Image téléchargée", width=300)
        else:
            if st.session_state.previous_file is not None:
                st.success("Fichier supprimé")
                # on supprime toutes les vars de sesssion + form
                for key in SESSION_VARS:
                    if st.session_state.get(key): del st.session_state[key]
                st.rerun()

        submit = st.button(
            label="Lancer le diagnostic",
            disabled=(uploaded_file is None),
            type = "primary"
        )

        if submit and uploaded_file:
            with st.spinner(text="Diagnostic en cours..."):
                # Appel à l'API pour le diagnostic
                diagnostic = call_api_diagnostic(uploaded_file)
                st.session_state.diagnostic = diagnostic
                st.success("Diagnostic terminée.")

                if DEBUG:
                    with st.expander("DEBUG Réponse API diagno"):
                        st.code(json.dumps(diagnostic, indent=2), language="json") 

    with col2:
        st.subheader("Carte des Parcelles")
        # coordonnées mises dans l'image de test : 43.767572, 3.847067 Héritage du Pic Saint Loup
        lon,lat,date = get_exif_data(uploaded_file)
        # on sauve en session
        st.session_state.img_long = lon
        st.session_state.img_lat = lat
        st.session_state.img_date = date

        # on affiche la carte si besoin
        if lon is not None and lat is not None:
            # Exemple simplifié : création d'une carte centrée sur les coordonnées EXIF
            m = folium.Map(location=[lat, lon], zoom_start=12, height=600, width=300, tiles=MAP_STYLE[0])
            folium.Marker([lat, lon], popup="Parcelle").add_to(m)
            st_folium(m, height=600)
        else:
            st.warning("Aucune donnée de localisation trouvée dans l'image.")

    ############ SECTION RESULTAT DIAGNO ##########
    st.divider()

    if st.session_state.diagnostic:
        # ATTENTION renvoie un dict et pas une liste de dict
        diagno = st.session_state.diagnostic
        with st.container(border=True, width="stretch", key="container_diagno"):
            if 'error' in diagno.keys():
                st.write(f"Error {diagno['status_code']}")
            elif 'predictions' in diagno.keys():
                predictions = diagno['predictions']
                best_predict = predictions[0]
                st.write("### Diagnostic :")
                col11,col12 = st.columns(2)
                with col11:
                    disease = best_predict.get('disease','N/A')
                    st.metric(label="Maladie détectée", value=DISEASE_TRANSLATION[disease])
                with col12:
                    confidence = best_predict.get('confidence', 0)
                    st.metric(label="Indice de confiance", value=f"{confidence*100:.1f}%")
        
        st.divider()
        
        # affichage du formulaire
        with st.form(key="vitiscan_form", width="stretch"):
            
            st.write("### Plan d'actions :")

            mode = st.selectbox("Mode", OPTIONS_MODE, index=1)
            severity = st.selectbox("Sévérité", OPTIONS_SEVERITY, index=1)
            area_ha = st.slider(label="Surface (ha)", min_value=0.1, max_value=5.0, value=0.5, step=0.1)

            # rendre les champs invisibles
            placeholder = st.empty()
            with placeholder.container():
                if 'predictions' in diagno.keys():
                    predictions = diagno['predictions']
                    best_predict = predictions[0]
                    cnn_label = st.text_input("cnn_label", best_predict.get("disease", "normal"), disabled=True)
                else:
                    cnn_label = st.text_input("cnn_label", "N/A", disabled=True)
                date_iso = st.text_input("date_iso", st.session_state.img_date, disabled=True)
                debug = st.checkbox("Inclure le raw LLM output (debug)", value='hidden')
            if not DEBUG:
                placeholder.empty()
            
            submitted = st.form_submit_button("Demander un plan d'actions", type="primary", key="button_action_plan")

            # construction du payload JSON à partir du form
            diagno_payload = {
                "cnn_label": cnn_label,
                "mode": mode,
                # TODO utiliser l'index de la combo
                #"mode": OPTIONS_MODE.index(mode)
                "severity": severity,
                # TODO utiliser l'index de la combo
                #"severity": OPTIONS_SEVERITY.index(severity),
                "area_m2": area_ha * 10000,
                "date_iso": date_iso,
                "location": f"{st.session_state.img_lat},{st.session_state.img_long}"
            }
            st.session_state.payload = diagno_payload
            
            # dès que le bouton est cliqué et que le payload est présent
            # on fait l'appel à l'API /solutions
            if submitted and st.session_state.payload :
                if DEBUG:
                    with st.expander("DEBUG Requête envoyée"):
                        st.code(json.dumps(diagno_payload, indent=2), language="json")

                # TODO rajouter try/except
                #if (cnn_label != "normal") or (cnn_label != "N/A"):
                with st.spinner(text="Calcul du plan en cours..."):
                    try:
                        response = call_api_solutions(diagno_payload)
                        st.session_state.solutions = response
                        st.success("Plan d'action terminé.")
                    except:
                        st.error("Impossible de calculer le plan d'actions")
                if DEBUG:
                    with st.expander("DEBUG Réponse API solutions"):
                        st.code(json.dumps(response, indent=2), language="json")
                #else:
                #    st.write("Aucun plan d'action.")
    
    ########## SECTION RESULTATS SOLUTIONS / TRAITEMENTS ########
    st.divider()

    if st.session_state.solutions:
        with st.container(border=True, width="stretch", key="container_solutions"):
            if "data" in st.session_state.solutions:
                d = st.session_state.solutions["data"]

                with st.expander("### Résumé traitement", width='stretch'):
                    st.markdown(f"**Maladie détectée** : {DISEASE_TRANSLATION[d.get('cnn_label', 'N/A')]}")
                    st.markdown(f"**Gravité** : {d.get('severity', '')}")
                    st.markdown(f"**Mode** : {d.get('mode', '')}")
                    st.markdown(f"**Saison** : {d.get('season', '')}")
                    if "treatment_plan" in d and d["treatment_plan"]:
                        tp = d['treatment_plan']
                        if "dose_l_ha" in tp and tp['dose_l_ha']:
                            st.markdown(f"- **Dose par ha** : {tp['dose_l_ha']} L/ha")
                            st.markdown(f"- **Surface** : {tp.get('area_m2')} m2")
                            st.markdown(f"- **Volume total estimé** : {tp.get('volume_bouillie_l_ha')} L")

                with st.expander("### Actions de traitement", width='stretch'):
                    if "treatment_actions" in d and d["treatment_actions"]:
                        for action in d["treatment_actions"]:
                            if action:
                                st.markdown(f"- {action}")

                with st.expander("### Mesures préventives"):
                    if "preventive_actions" in d and d["preventive_actions"]:
                        for action in d["preventive_actions"]:
                            if action:
                                st.markdown(f"- {action}")

                with st.expander("### Avertissements"):
                    if "warnings" in d and d["warnings"]:
                        for w in d["warnings"]:
                            if w:
                                st.markdown(f"- {w}")

                #with st.expander("### Texte de conseil"):
                #    if "advice_text" in d and d['advice_text']:
                #        st.write(d["advice_text"])


if __name__ == "__main__":
    main()

