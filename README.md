# dyndns-docker-client

Ein einfach konfigurierbarer DynDNS-Client als Docker-Container. Unterstützt die automatische Aktualisierung von DNS-Einträgen über Umgebungsvariablen.

## Features

- Unterstützt DynDNS-Update via Benutzer/Passwort oder API-Key
- IP-Erkennung automatisch oder manuell einstellbar
- Frei konfigurierbarer Intervall

## Nutzung

### Docker-Image bauen
```bash
docker build -t dyndns-client .
