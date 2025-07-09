# Log-Level Konfiguration Erklärung

## Problem
Der Benutzer hatte `loglevel: INFO` gesetzt, aber keine INFO-Nachrichten erschienen in der Log-Datei. Das lag daran, dass es zwei `loglevel` Einstellungen in der config.example.yaml gab, die sich widersprachen.

## Lösung
Die config.example.yaml hatte folgende widersprüchliche Einstellungen:

```yaml
# Erste Definition (Zeile 45)
loglevel: INFO

# Zweite Definition (Zeile 69) - überschreibt die erste!
loglevel: "WARNING"
```

Die zweite Definition überschrieb die erste, weshalb nur WARNING, ERROR und CRITICAL Nachrichten geloggt wurden, aber nicht die INFO-Nachrichten über IP-Updates.

## Korrekte Konfiguration

### Für INFO-Level Logging (empfohlen):
```yaml
logging:
  enabled: true
  file: "/app/config/dyndns.log"  # oder "/var/log/dyndns/dyndns.log"
  max_size_mb: 10
  backup_count: 3

consolelevel: "INFO"  # Console-Ausgabe: INFO und höher
loglevel: "INFO"      # Log-Datei: INFO und höher
```

### Für ausführliches Logging:
```yaml
consolelevel: "TRACE"  # Console zeigt alles
loglevel: "DEBUG"      # Log-Datei zeigt DEBUG und höher
```

### Für minimales Logging:
```yaml
consolelevel: "INFO"    # Console zeigt INFO und höher  
loglevel: "WARNING"     # Log-Datei nur Warnungen und Fehler
```

## Log-Level Hierarchie
- **TRACE**: Routine-Nachrichten (z.B. "Next run in 60 seconds...")
- **DEBUG**: Debug-Informationen (z.B. API-Responses)
- **INFO**: Wichtige Ereignisse (z.B. IP-Updates, erfolgreiche Updates)
- **WARNING**: Warnungen (z.B. "No method configured")
- **ERROR**: Fehler (z.B. failed API calls)
- **CRITICAL**: Kritische Fehler (z.B. Konfigurationsfehler)

## Was wird bei INFO-Level geloggt?
- Erfolgreiche IP-Updates: `Provider 'cloudflare' updated successfully. New IP: 124.120.46.43`
- IP-Änderungen: `New IP detected: 124.120.46.43 (previous: 124.120.45.154)`
- Provider-Responses: `ipv64 response: {"info":"good","status":"success"}`
- Startup-Meldungen: `Using primary service to determine IPv4: https://api.ipify.org`

## Hinweis für Docker
Stellen Sie sicher, dass der Log-Pfad im Container verfügbar ist:
```yaml
# docker-compose.yml
volumes:
  - ./config:/app/config  # Log-Datei wird in ./config/dyndns.log erstellt
```
