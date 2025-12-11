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
API_DIAGNO = os.getenv("API_DIAGNO", "https://localhost:4000").replace('"','')
API_SOLUTIONS = os.getenv("API_SOLUTIONS", "https://localhost:9000").replace('"','')

# 
HEADERS = {
    'Accept-Encoding':'gzip, deflate, br, zstd',
    'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0'
}

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
                else:
                    st.write("Pas de données de localisation dans l'image")
        else:
            st.write("Pas de données de localisation dans l'image")
    except Exception as e:
        #st.error(f"Erreur EXIF: {e}")
        pass
    return (0,0)

def call_mock_api_diagnostic(image):
    """Appel API pour obtenir un diagnostic."""
    if MOCK == 1:
        # ATTENTION ici en mock je renvoie un tableau de dictionnaires
        diagnostic = [{'disease':'Mildiou', 'confidence':0.96 }, {'disease':'Anthracnose', 'confidence':0.75 }]
        #diagnostic = {'disease':'Anthracnose', 'confidence':0.75, 'model_version': 'Resnet34_30ep_v1' }
        return diagnostic
    else:
        # ATTENTION ici l'API renvoie un dictionnaire seulement
        files = {"file": image}
        url = API_DIAGNO + "/diagno"
        st.write('url=', url)
        response = requests.post(url, files=files, verify=False, headers=HEADERS)
        if response.status_code != 200:
            print(f'Error: {response.status_code}')
            print(response.text)
            return {'error': response.text, 'status_code': response.status_code }
        else:
            return response.json()

def call_mock_api_treatment(disease):
    """Appel API pour obtenir les traitements."""
    if MOCK == 1:
        treatment = TREATMENTS[disease]
        return treatment
    else:
        response = requests.post(f"{API_SOLUTIONS}/treatment", json={"disease": disease}, verify=False)
        if response.status_code != 200:
            print(f'Error: {response.status_code}')
            print(response.text)
        else:
            return response.json()

def main():
    st.write(f"CONFIGURATION DEBUG\n{API_DIAGNO}\n{API_SOLUTIONS}\n{MOCK}")
    st.title("VitiScan Pro: Diagnostic & Gestion des Vignes")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Diagnostic Foliaire & Actions")
        uploaded_file = st.file_uploader("Téléchargez une photo de feuille de vigne", type=["jpg", "png","jpeg"])

        if uploaded_file:
            st.image(uploaded_file, caption="Image téléchargée", width=300)

            # Appel à l'API pour le diagnostic
            diagnostic = call_mock_api_diagnostic(uploaded_file)
            if 'error' in diagnostic.keys():
                st.write(f"Error {diagnostic['status_code']}")
            else:
                st.write("### Maladies détectées :")
                if diagnostic is list:
                    # ATTENTION cas du MOCK=1 qui renvoie une liste de dict
                    for disease in diagnostic:
                        if st.button(disease["disease"]):
                            treatment = call_mock_api_treatment(disease["disease"])
                            st.write("#### Traitements recommandés :")
                            st.html(treatment)
                else:
                    # ATTENTION cas du MOCK=0 qui renvoie un dict
                    if st.button(diagnostic["disease"]):
                            treatment = call_mock_api_treatment(diagnostic["disease"])
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

