---
title: VITISCAN PRO
emoji: 🍇
colorFrom: green
colorTo: purple
sdk: docker
app_file: app.py
pinned: false
---

# WebUI-Streamlit — Vitiscan

Streamlit web interface for the Vitiscan MLOps project. Farmers upload a grape leaf photo
and receive a disease diagnosis and a personalized treatment plan in return.
Deployed on HuggingFace Spaces as a Docker container.

## Role in the Vitiscan architecture

```
Farmer
  │
  │  uploads leaf photo
  ▼
WebUI-Streamlit (this repo)
  │                        │
  │ POST /diagno           │ POST /solutions
  ▼                        ▼
Diagnostic API      Treatment Plan API
(ResNet18 CNN)      (RAG + LLM)
  │                        │
  └────────────────────────┘
           │
           ▼
    Results displayed
    to the farmer
```

The Streamlit app is a **pure frontend** — it holds no ML logic. It delegates everything
to the two backend APIs and displays the results.

## What the app does

A farmer goes through three steps in a single session:

1. **Upload** a grape leaf photo — the image is sent to the Diagnostic API which returns
   the detected disease and a confidence score
2. **Parcel map** — GPS coordinates are extracted from the image EXIF metadata and displayed
   on an interactive Folium map
3. **Treatment plan** — the farmer selects farming mode (conventional / organic), severity,
   and parcel area, then submits to the Treatment Plan API which returns product recommendations,
   dosage, preventive measures and warnings

## File structure

```
WebUI-Streamlit/
├── app.py                    # Main Streamlit application 
├── .streamlit/
│   └── config.toml           # Streamlit theme
├── Dockerfile                # Container image
├── requirements.txt          # Dependencies
├── environment.yml           # Local Conda environment
├── .env.template             # Required environment variables
├── .gitattributes            # Git LFS for binary ML files
├── .gitignore                # Python, secrets, IDE, OS artifacts
└── README.md                 # This file
```

## Environment variables

Copy `.env.template` to `.env` and fill in the values before running locally.

| Variable | Description | Default |
|---|---|---|
| `API_DIAGNO` | Diagnostic API base URL | `http://localhost:8000` |
| `API_SOLUTIONS` | Treatment Plan API base URL | `http://localhost:9000` |
| `MOCK` | `1` = run without calling APIs (UI development) | `1` |
| `DEBUG` | `1` = show raw API payloads and LLM output in UI | `0` |

> **Mock mode** (`MOCK=1`): the app returns hardcoded responses instead of calling the APIs.
> Useful for developing the UI without having to run the backend services locally.

> **Debug mode** (`DEBUG=1`): exposes hidden form fields and shows raw JSON payloads
> in expandable sections throughout the UI.

## Run locally

**With Python / Conda:**
```bash
# 1. Create the Conda environment
conda env create -f environment.yml
conda activate vitiscan_streamlit

# 2. Configure environment variables
cp .env.template .env
# Edit .env — set API_DIAGNO and API_SOLUTIONS to your local or deployed API URLs

# 3. Start the app
streamlit run app.py
```

App available at `http://localhost:7860`

**With Docker:**
```bash
# 1. Build the image
docker build -t vitiscan-streamlit .

# 2. Run the container
docker run --rm -p 7860:7860 --env-file .env vitiscan-streamlit
```

## Deployment

Every push to `main` automatically deploys to HuggingFace Spaces.
The app is live at: `https://mouniat-vitiscanpro-streamlit.hf.space`

HuggingFace Spaces secrets to configure (Space Settings → Variables and secrets):

| Variable | Value |
|---|---|
| `API_DIAGNO` | Deployed Diagnostic API URL |
| `API_SOLUTIONS` | Deployed Treatment Plan API URL |
| `MOCK` | `0` |
| `DEBUG` | `0` |

## app.py structure

The application is a single file organized in four sections:

| Section | What it does |
|---|---|
| **Configuration** | Loads env vars, defines constants, configures logging |
| **Helper functions** | `get_exif_data()`, `call_api_diagnostic()`, `call_api_solutions()`, `get_diseases()` |
| **Main UI** | Two-column layout: file uploader + map, then diagnosis results + treatment form |
| **Results display** | Treatment plan, preventive measures, warnings — all in expandable sections |

Session state is used to persist data across Streamlit reruns within a session
(uploaded file, diagnosis result, treatment plan, GPS coordinates).
Uploading a new file triggers `reset_session()` which clears all state.

## Requirements

- Python 3.11
- Streamlit 1.45.0
- See `requirements.txt` for full pinned dependency list

## Author

**Mounia Tonazzini** — Agronomist Engineer & Data Scientist and Data Engineer

- HuggingFace: [huggingface.co/MouniaT](https://huggingface.co/MouniaT)
- LinkedIn: [www.linkedin.com/in/mounia-tonazzini](www.linkedin.com/in/mounia-tonazzini)
- GitHub: [github/Mounia-Agronomist-Datascientist](https://github.com/Mounia-Agronomist-Datascientist)
- Email : mounia.tonazzini@gmail.com