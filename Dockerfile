FROM python:3.11-slim

WORKDIR /app
RUN mkdir -p /app/config
COPY update_dyndns.py /app/update_dyndns.py
COPY config.example.yaml /app/config.example.yaml
COPY config.example.yaml /app/config/config.yaml

# Installiere benötigte Python-Module
RUN pip install --no-cache-dir requests pyyaml

# Standard-Startbefehl (ohne entrypoint.sh)
CMD ["python", "/app/update_dyndns.py"]
