# app.py
import streamlit as st
import requests
import folium
from PIL import Image, ExifTags
from streamlit_folium import st_folium

# API URL (à adapter selon déploiement)
# TODO récupérer ces variables dans le .env avec dotenv
# sur HuggingFace le port sera forcément 7860 mais des hostnames différents
# alors qu'en local ce sera l'inverse
API_DIAGNO="http://localhost:8000"
API_SOLUTIONS="http://localhost:9090"

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
                    #print(degre, minute, seconde)
                    lat = int(degre) + int(minute)/60 + int(seconde)/3600
                    degre,minute,seconde = value[4]
                    #print(degre, minute, seconde)
                    lon = int(degre) + int(minute)/60 + int(seconde)/3600
                    return (lon,lat)
    except Exception as e:
        st.error(f"Erreur EXIF: {e}")
    return (0,0)

def call_mock_api_diagnostic(image):
    """Appel API pour obtenir un diagnostic."""
    files = {"file": image}
    response = requests.post(f"{API_DIAGNO}/diagnostic", files=files)
    return response.json()

def call_mock_api_treatment(disease):
    """Appel API pour obtenir les traitements."""
    response = requests.post(f"{API_SOLUTIONS}/treatment", json={"disease": disease})
    return response.json()

def main():
    st.title("VitiScan Pro: Diagnostic & Gestion des Vignes")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Diagnostic Foliaire & Actions")
        uploaded_file = st.file_uploader("Télchargez une photo de feuille de vigne", type=["jpg", "png"])

        if uploaded_file:
            st.image(uploaded_file, caption="Feuille téléchargée", width=300)

            # Appel à l'API pour le diagnostic
            # A DECOMMENTER lorsque API diagno opérationnelle
            #diagnostic = call_mock_api_diagnostic(uploaded_file)
            diagnostic = [{'disease':'mildiou', 'probability':0.96 }]
            st.write("### Maladies détectées :")
            for disease in diagnostic:
                if st.button(disease["disease"]):
                    # A DECOMMENTER lorsque API treatment opérationnelle
                    #treatment = call_mock_api_treatment(disease["disease"])
                    treatment = "1. Curatif: Boullie bordelaise bla bla bla bla bla"
                    st.write("#### Traitements recommandés :")
                    #st.write(treatment["treatment"])

    with col2:
        st.subheader("Carte Interactive des Parcelles")
        # coordonnées mises dans l'image de test : 43.767572, 3.847067 Héritage du Pic Saint Loup
        lon,lat = get_exif_data(uploaded_file)
        if lon is not None and lat is not None:
            # Exemple simplifié : création d'une carte centrée sur les coordonnées EXIF
            #print("long=", lon, " lat=", lat)
            m = folium.Map(location=[lat, lon], zoom_start=12)
            folium.Marker([lat, lon], popup="Parcelle").add_to(m)
            st_folium(m, width=500, height=500)
        else:
            st.warning("Aucune donnée de localisation trouvée dans l'image.")

if __name__ == "__main__":
    main()

