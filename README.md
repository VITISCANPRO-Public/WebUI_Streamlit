# Projet final FS37 - VitiScan WebUI avec Streamlit

__Auteurs__ : Mounia, Inti, Samuel, Guillaume

## préparation environnement

- si ce n'est pas déjà fait par défaut, activer conda
`source ~/app/miniconda3/etc/profile.d/conda.sh && conda activate`

- vous devez avoir un prompt du type
`(base)$`

- créer l'environnement python avec conda

`(base)$ conda env create -n vitiscan_streamlit --file env_vitiscan_streamlit.yml`

- activer l'environnement

`(base)$ conda activate vitiscan_streamlit`

- copier le .env_template en .env et y mettre ses clés s'il y en a

- si vous voulez ajouter ou retirer une dépendance :
  - modidier le fichier d'env env_vitiscan_streamlit.yml
  - lancer (quelque soit l'env ou vous etes : `$ conda env update -n vitiscan_streamlit --file env_vitiscan_streamlit.yml`

## Image Docker pour le développement

## Déploiement de l'image Docker sur HuggingFace





docker build . -t streamlit_vitiscan
