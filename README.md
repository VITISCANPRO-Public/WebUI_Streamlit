# Vitiscan Pro — Web Interface

Streamlit web application for grape leaf disease diagnosis and treatment planning.
Part of the **Vitiscan MLOps pipeline**.

## Overview

Farmers upload a grape leaf photo and get:
1. **Disease diagnosis** — CNN model prediction with confidence score
2. **Parcel map** — GPS coordinates extracted from image EXIF data
3. **Treatment plan** — RAG-LLM recommendations based on disease, severity and farming mode

## Project Structure
```
WebUI-Streamlit/
├── app.py              # Main Streamlit application
├── .streamlit/
│   └── config.toml     # Streamlit theme configuration
├── Dockerfile
└── requirements.txt
```

## Quickstart

**1. Install dependencies**
```bash
pip install -r requirements.txt
```

**2. Configure your `.env`**
```bash
cp .env.example .env
# Fill in API_DIAGNO and API_SOLUTIONS URLs
```

**3. Run locally**
```bash
streamlit run app.py
```

App available at `http://localhost:8501`

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `API_DIAGNO` | Diagnostic API URL | `https://localhost:4000` |
| `API_SOLUTIONS` | Treatment Plan API URL | `https://localhost:9000` |
| `MOCK` | Enable mock mode (1=on) | `0` |
| `DEBUG` | Enable debug mode (1=on) | `0` |

> **Mock mode** (`MOCK=1`): runs the app without calling the APIs, useful for UI development.

## Deployment

Deployed on HuggingFace Spaces (Docker) at:  
`https://mouniat-vitiscanpro-streamlit.hf.space`

## Requirements

- Python 3.11
- Streamlit >= 1.40.0
- See `requirements.txt` for full list