FROM python:3.11-slim

WORKDIR /app

# Installiere benötigte Python-Module
RUN pip install --no-cache-dir requests pyyaml

# Kopiere Quellcode und Beispiel-Konfiguration ins Image
COPY update_dyndns.py /app/update_dyndns.py
COPY notify.py /app/notify.py
COPY config.example.yaml /app/config.example.yaml

# Erstelle Config-Ordner (falls nicht durch Volume überschrieben)
RUN mkdir -p /app/config

# Standard-Startbefehl
CMD ["python", "/app/update_dyndns.py"]
