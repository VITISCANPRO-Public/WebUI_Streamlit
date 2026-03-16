FROM python:3.11-slim

# Disable output buffering and .pyc generation
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt ./
COPY tests/requirements.txt ./tests/
# Install test dependencies only — much lighter than the full app image
RUN pip install --upgrade pip && \
    pip install -r tests/requirements.txt

# Copy source files required to import app.py
COPY app.py ./
COPY tests/ ./tests/

# Run pytest
CMD ["python", "-m", "pytest", "tests/", "-v", "--tb=short"]