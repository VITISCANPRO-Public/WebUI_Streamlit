FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y vim nano unzip curl \
    && rm -rf /var/lib/apt/lists/*

# THIS IS SPECIFIC TO HUGGINFACE
# We create a new user named "user" with ID of 1000
RUN useradd -m -u 1000 user
RUN mkdir -p /home/user/app/.streamlit

USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# We set working directory to $HOME/app (<=> /home/user/app)
WORKDIR $HOME/app

# Install basic dependencies
#RUN pip install boto3 pandas gunicorn streamlit scikit-learn matplotlib seaborn plotly
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && pip install --no-cache-dir -r /tmp/requirements.txt

# Copy all local files to /home/user/app with "user" as owner of these files
# Always use --chown=user when using HUGGINGFACE to avoid permission errors
COPY --chown=user Dockerfile app.py README.md $HOME/app/
COPY --chown=user .streamlit/config.toml $HOME/app/.streamlit/

EXPOSE 7860

CMD ["/bin/bash", "-c", "streamlit run app.py --server.port=$STREAMLIT_SERVER_PORT --server.address=0.0.0.0"]

# en prod préférable d'utiliser un entrypoint
#ENTRYPOINT ["/bin/bash", "-c", "streamlit run app.py --server.port=$PORT --server.address=0.0.0.0"]