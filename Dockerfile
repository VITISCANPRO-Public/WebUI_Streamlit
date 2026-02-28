FROM python:3.11-slim

# Disable output buffering, .pyc generation and pip cache for a cleaner image
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
# - curl : required by the HEALTHCHECK
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user (UID 1000 required by HuggingFace Spaces)
RUN useradd -m -u 1000 user

USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && \
    pip install -r /tmp/requirements.txt

# Copy application files
COPY --chown=user app.py README.md requirements.txt ./

# Copy Streamlit theme configuration
# COPY creates the .streamlit/ directory automatically with the correct ownership
COPY --chown=user .streamlit/config.toml .streamlit/

EXPOSE 7860

# Health check — Streamlit exposes /_stcore/health natively
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:7860/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0"]