FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl unzip \
    && rm -rf /var/lib/apt/lists/*

# HuggingFace requires a non-root user with ID 1000
RUN useradd -m -u 1000 user
RUN mkdir -p /home/user/app/.streamlit

USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && pip install --no-cache-dir -r /tmp/requirements.txt

COPY --chown=user app.py README.md requirements.txt Dockerfile $HOME/app/
COPY --chown=user .streamlit/config.toml $HOME/app/.streamlit/

EXPOSE 7860

CMD ["streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0"]