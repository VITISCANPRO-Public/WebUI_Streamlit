import os
import json
import streamlit as st
import requests
import folium
from PIL import Image, ExifTags
from streamlit_folium import st_folium
from dotenv import load_dotenv

load_dotenv()

# API URL (à adapter selon déploiement)
MOCK = int(os.getenv("MOCK", "0"))
API_DIAGNO = os.getenv("API_DIAGNO", "https://localhost:8000")
API_SOLUTIONS = os.getenv("API_SOLUTIONS", "https://localhost:9000")

# mock data
TREATMENTS = { 'Mildiou' : '<ol><li>Curatif: Boullie bordelaise bla bla bla bla bla</li><li>Préventif: sdkfsdmfkj</li></ol>',
                'Anthracnose' : '<ol><li>Curatif: bla bla bla bla</li><li>Préventif: ipsum loredum etc.</li></ol>'}

def get_exif_data(image):
    """Extrait les données EXIF (latitude, longitude) de l'image."""
    try:
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
                    return (lon,lat)
    except Exception as e:
        st.error(f"Erreur EXIF: {e}")
    return (0,0)

def call_mock_api_diagnostic(image):
    """Appel API pour obtenir un diagnostic."""
    files = {"file": image}
    if MOCK == 1:
        diagnostic = [{'disease':'Mildiou', 'confidence':0.96 }, {'disease':'Anthracnose', 'confidence':0.75 }]
        return diagnostic
    else:
        response = requests.post(f"{API_DIAGNO}/diagno", files=files, verify=False)
        return response.json()

def call_mock_api_treatment(disease):
    """Appel API pour obtenir les traitements."""
    if MOCK == 1:
        treatment = TREATMENTS[disease]
        return treatment
    else:
        response = requests.post(f"{API_SOLUTIONS}/treatment", json={"disease": disease}, verify=False)
        return response.json()

def main():
    st.title("VitiScan Pro: Diagnostic & Gestion des Vignes")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Diagnostic Foliaire & Actions")
        uploaded_file = st.file_uploader("Téléchargez une photo de feuille de vigne", type=["jpg", "png","jpeg"])

        if uploaded_file:
            st.image(uploaded_file, caption="Feuille téléchargée", width=300)

            # Appel à l'API pour le diagnostic
            diagnostic = call_mock_api_diagnostic(uploaded_file)
            st.write("### Maladies détectées :")
            for disease in diagnostic:
                if st.button(disease["disease"]):
                    treatment = call_mock_api_treatment(disease["disease"])
                    st.write("#### Traitements recommandés :")
                    st.html(treatment)

    with col2:
        st.subheader("Carte Interactive des Parcelles")
        # coordonnées mises dans l'image de test : 43.767572, 3.847067 Héritage du Pic Saint Loup
        lon,lat = get_exif_data(uploaded_file)
        if lon is not None and lat is not None:
            # Exemple simplifié : création d'une carte centrée sur les coordonnées EXIF
            m = folium.Map(location=[lat, lon], zoom_start=10)
            folium.Marker([lat, lon], popup="Parcelle").add_to(m)
            st_folium(m, width=500, height=500)
        else:
            st.warning("Aucune donnée de localisation trouvée dans l'image.")

if __name__ == "__main__":
    main()

