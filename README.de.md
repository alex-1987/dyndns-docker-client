# DynDNS Docker Client

> :gb: For the English documentation see [README.md](README.md)

---

## Inhaltsverzeichnis

1. [Überblick](#überblick)
2. [Features](#features)
3. [Loglevel & Consolelevel](#loglevel--consolelevel)
4. [Schnellstart (Docker & Compose)](#schnellstart-docker--compose)
5. [Konfiguration](#konfiguration-configconfigyaml)
   - [Grundlegende Optionen](#grundlegende-optionen)
   - [Provider-Konfiguration](#provider-konfiguration)
   - [Benachrichtigungen & Cooldown](#benachrichtigungen--cooldown)
   - [Provider-Update beim Neustart nur bei IP-Änderung](#provider-update-beim-neustart-nur-bei-ip-änderung)
6. [Beispiele](#beispiele)
7. [Fehlerbehandlung & Tipps](#fehlerbehandlung--tipps)
8. [Mitmachen & Support](#mitmachen--support)
9. [Lizenz](#lizenz)

---

## Überblick

Dieses Projekt ist ein flexibler DynDNS-Client für verschiedene Provider (z.B. Cloudflare, ipv64, DuckDNS, NoIP, Dynu) und läuft als Docker-Container.  
Es unterstützt IPv4 und optional IPv6, prüft regelmäßig die öffentliche IP und aktualisiert die DNS-Einträge bei den konfigurierten Diensten.

**Funktionsweise:** Der Client prüft alle `timer` Sekunden (Standard: 300) die öffentliche IP-Adresse. Hat sich die IP seit dem letzten Check geändert, werden alle konfigurierten Provider aktualisiert. Ist die IP gleich geblieben, wird kein Update gesendet (außer du hast es anders konfiguriert). Alle Aktionen, Fehler und Benachrichtigungen werden geloggt.

---

## Features

- **Mehrere Provider:** Unterstützt Cloudflare, ipv64, DuckDNS, NoIP, Dynu und andere DynDNS2-kompatible Dienste.
- **IPv4 & IPv6:** Aktualisiert A- und AAAA-Records, wenn gewünscht.
- **Automatisches Nachladen:** Änderungen an der `config.yaml` werden automatisch erkannt und übernommen.
- **Flexible Konfiguration:** Jeder Provider kann beliebig benannt werden, der Typ wird über das Feld `protocol` gesteuert.
- **Detailliertes Logging:** Zeigt an, ob ein Update durchgeführt wurde, nicht nötig war oder ein Fehler auftrat.
- **Benachrichtigungs-Cooldown:** Jeder Dienst kann einen eigenen Cooldown für Benachrichtigungen erhalten.
- **Provider-Update beim Neustart nur bei IP-Änderung:** Spart unnötige Requests und schützt vor Rate-Limits.
- **Netzwerkschnittstellen-Unterstützung:** IPs können direkt von lokalen Interfaces abgerufen werden.
- **Flexibles Logging:** Separates Logging für Konsole und Datei mit Rotation.
- **IP-Validierung:** Automatische Validierung aller abgerufenen IP-Adressen.
- **🔄 Netzwerk-Resilienz:** Verbesserte Stabilität bei Netzwerkproblemen

---

## Log Levels

Konfiguriere das Logging in deiner `config.yaml`:

```yaml
loglevel: "INFO"        # Dateiloglevel  
consolelevel: "INFO"    # Konsolen-Ausgabelevel
```

**Verfügbare Level:**
- **TRACE** - Sehr detailliert, zeigt jeden IP-Check
- **DEBUG** - Technische Details, Timer, Fehlersuche
- **INFO** - Standard für Produktion, wichtige Ereignisse
- **WARNING** - Probleme und Netzwerkfehler
- **ERROR** - Schwerwiegende Fehler die Aufmerksamkeit erfordern
- **CRITICAL** - Fatale Fehler die das Programm stoppen

**Schnelle Konfiguration:**
```yaml
# Produktion: ruhige Konsole, detaillierte Logs
consolelevel: "WARNING"
loglevel: "INFO"

# Entwicklung: alles anzeigen
consolelevel: "DEBUG"
loglevel: "TRACE"
```

### Beispiel-Konfiguration für loglevel und consolelevel

```yaml
loglevel: TRACE         # Dateiloglevel: alles loggen, inkl. Routine-Meldungen
consolelevel: INFO      # Konsolenlevel: nur wichtige Infos und höher anzeigen
```

- `loglevel` steuert, was in die Logdatei geschrieben wird (sofern aktiviert).
- `consolelevel` steuert, was auf der Konsole ausgegeben wird.
- Setze einen der Werte auf `TRACE`, um alle Routine-/Statusmeldungen zu sehen.
- Setze einen der Werte auf `DEBUG`, um technische Details und Timer-Meldungen zu sehen.

### Praktische Empfehlungen

**Kombinationsbeispiele:**
```yaml
# Beispiel 1: Detaillierte Konsole, kompakte Datei
consolelevel: "DEBUG"    # Konsole: Timer + Details sichtbar
loglevel: "WARNING"      # Datei: nur Probleme dauerhaft speichern

# Beispiel 2: Kompakte Konsole, vollständige Datei  
consolelevel: "INFO"     # Konsole: nur wichtige Events
loglevel: "TRACE"        # Datei: alles für spätere Analyse

# Beispiel 3: Vollständige Überwachung
consolelevel: "TRACE"    # Konsole: alle Details live sehen
loglevel: "TRACE"        # Datei: vollständige Aufzeichnung
```

---
- Dateilogs müssen im Abschnitt `logging` der Config aktiviert werden, damit Logs in eine Datei geschrieben werden.

Beispiel-Konfiguration:
```yaml
loglevel: "INFO"
consolelevel: "WARNING"
logging:
  enabled: true
  file: "/var/log/dyndns/dyndns.log"
```

---

## Schnellstart (Docker & Compose)

### Offizielles Image von Docker Hub

```sh
docker pull alexfl1987/dyndns:latest-stable
```

Starte den Container mit deiner eigenen Konfiguration:

```sh
docker run -u 1000:1000 \
  -d --name dyndns-client \
  -v $(pwd)/config/config.yaml:/app/config/config.yaml \
  alexfl1987/dyndns:latest-stable
```
---

### Docker Compose Beispiel

Lege eine Datei `docker-compose.yml` an:

```yaml
services:
  dyndns-client:
    image: alexfl1987/dyndns:latest-stable
    container_name: dyndns-client
    user: "1000:1000"
    volumes:
      - ./config:/app/config
    restart: unless-stopped
```

Starte mit:

```sh
docker compose up -d
```

---

## Konfiguration (`config/config.yaml`)

**WICHTIG:**  
Lege im Ordner `config` eine Datei `config.yaml` an!  
Der Inhalt sollte sich an der mitgelieferten `config.example.yaml` orientieren.

### Grundlegende Optionen

```yaml
timer: 300  # Intervall in Sekunden für die IP-Prüfung
ip_service: "https://api.ipify.org"  # Service zum Abrufen der öffentlichen IPv4
ip6_service: "https://api64.ipify.org"  # (Optional) Service zum Abrufen der öffentlichen IPv6
skip_update_on_startup: true  # Siehe unten!
```

### Netzwerk-Interface-Konfiguration (Alternative zu IP-Services)

Statt externe IP-Services zu verwenden, kann der Client IP-Adressen direkt von Netzwerk-Interfaces lesen:

```yaml
# Netzwerk-Interface anstelle eines externen Services für IPv4
interface: "eth0"  # Ersetze durch den Namen deines tatsächlichen Interfaces

# Netzwerk-Interface anstelle eines externen Services für IPv6 (optional)
interface6: "eth0"  # Ersetze durch den Namen deines tatsächlichen Interfaces
```

**Voraussetzungen für Interface-Modus:**
- Docker muss mit `network_mode: host` laufen, um auf Host-Interfaces zugreifen zu können
- Das angegebene Interface muss existieren und eine gültige öffentliche IP-Adresse haben
- Für IPv6 werden link-lokale Adressen (fe80::/10) automatisch übersprungen

**Beispiel docker-compose.yml für Interface-Modus:**
```yaml
services:
  dyndns-client:
    image: alexfl1987/dyndns:latest-stable
    network_mode: host  # Erforderlich für Interface-Zugriff!
    volumes:
      - ./config:/app/config
```

**Hinweis:** Du kannst entweder `ip_service`/`ip6_service` ODER `interface`/`interface6` verwenden, nicht beides gleichzeitig.

### Provider-Konfiguration

```yaml
providers:
  - name: duckdns
    protocol: dyndns2
    url: "https://www.duckdns.org/update"
    token: "your-duckdns-token"
    domain: "example"
  - name: mein-cloudflare
    protocol: cloudflare
    zone: "deinedomain.tld"
    api_token: "dein_cloudflare_api_token"
    record_name: "sub.domain.tld"
  # ...weitere Provider siehe config.example.yaml...
```

### Benachrichtigungen & Cooldown

Du kannst Benachrichtigungen auf zwei Arten konfigurieren:

#### 1. Globale Benachrichtigungen (für alle Provider)
Konfiguriere Benachrichtigungen einmal im globalen `notify`-Bereich. Alle Provider verwenden standardmäßig diese Einstellungen.

#### 2. Provider-spezifische Benachrichtigungen  
Konfiguriere Benachrichtigungen individuell für jeden Provider. Provider-spezifische Einstellungen überschreiben globale Einstellungen.

Du kannst für **jeden Notification-Dienst** einen eigenen Cooldown (in Minuten) setzen, um Benachrichtigungs-Spam zu vermeiden.  
Nach einer Benachrichtigung wartet der jeweilige Dienst die angegebene Zeit, bevor wieder eine Nachricht gesendet wird.  
Ist kein Wert gesetzt oder `0`, gibt es **keinen Cooldown** für diesen Dienst.

```yaml
# Globale Benachrichtigungskonfiguration (wird von allen Providern verwendet, außer überschrieben)
notify:
  reset_cooldown_on_start: true  # Cooldown-Zähler wird beim Start zurückgesetzt
  discord:
    enabled: true
    webhook_url: "https://discord.com/api/webhooks/global-webhook"
    notify_on: ["ERROR", "CRITICAL"]
    cooldown: 30

providers:
  # Dieser Provider verwendet die globalen Benachrichtigungseinstellungen
  - name: normaler-provider
    protocol: cloudflare
    zone: "beispiel.de"
    api_token: "token123"
    record_name: "www.beispiel.de"
  
  # Dieser Provider hat eigene Benachrichtigungseinstellungen  
  - name: kritischer-provider
    protocol: cloudflare
    zone: "wichtig.de"
    api_token: "token456"
    record_name: "api.wichtig.de"
    # Provider-spezifische Benachrichtigungen überschreiben globale Einstellungen
    notify:
      discord:
        enabled: true
        webhook_url: "https://discord.com/api/webhooks/critical-webhook"
        notify_on: ["ERROR", "CRITICAL", "UPDATE"]  # Mehr Events für kritischen Provider
        cooldown: 0  # Kein Cooldown für kritische Benachrichtigungen
      email:
        enabled: true
        to: "admin@wichtig.de"
        # ... weitere E-Mail-Einstellungen
```

Mit  
```yaml
reset_cooldown_on_start: true
```
kannst du festlegen, dass beim Start des Containers alle Cooldown-Zähler zurückgesetzt werden.  
Setze diese Option auf `false`, um den Cooldown auch nach einem Neustart weiterlaufen zu lassen.

**Verfügbare Benachrichtigungsdienste:**
- **Discord:** Webhook-Benachrichtigungen zu Discord-Kanälen
- **Slack:** Webhook-Benachrichtigungen zu Slack-Kanälen
- **E-Mail:** SMTP E-Mail-Benachrichtigungen
- **Telegram:** Bot-Benachrichtigungen über Telegram API
- **ntfy:** Push-Benachrichtigungen über ntfy.sh
- **Webhook:** Benutzerdefinierte HTTP-Webhook-Aufrufe

**Hinweis:**  
- Die Cooldown-Zeit wird pro Dienst separat gespeichert.
- Die Option `reset_cooldown_on_start` gilt für alle Dienste gemeinsam.
- Nach einer Benachrichtigung wird der Cooldown für den jeweiligen Dienst gesetzt.
- Provider-spezifische Benachrichtigungseinstellungen überschreiben immer globale Einstellungen.

---

### Provider-Update beim Neustart nur bei IP-Änderung

Mit der Option  
```yaml
skip_update_on_startup: true
```
in deiner `config.yaml` werden beim **Start des Containers** Provider-Updates **nur dann durchgeführt, wenn sich die öffentliche IP seit dem letzten Lauf geändert hat**.  
Ist die IP gleich geblieben, werden keine unnötigen Updates gemacht.  
Wenn die Option auf `false` steht oder fehlt, wird beim Start immer ein Update gemacht – unabhängig von der IP.

Die zuletzt bekannte IP wird im Container unter `/tmp` gespeichert.

**Hinweis:**  
- Diese Option kann nützlich sein, um unnötige Update-Anfragen zu vermeiden, wenn sich die IP nicht geändert hat.
- Funktioniert nur, wenn die IP von einem externen Dienst (wie ipify) abgerufen wird.

---

## Beispiele

### Nur IPv4, nur IPv6 oder beides aktualisieren

- **Nur IPv4:**  
  ```yaml
  ip_service: "https://api.ipify.org"
  ```
- **Nur IPv6:**  
  ```yaml
  ip6_service: "https://api64.ipify.org"
  ```
- **Beides:**  
  ```yaml
  ip_service: "https://api.ipify.org"
  ip6_service: "https://api64.ipify.org"
  ```

Wenn du einen der beiden Einträge weglässt, wird nur die jeweils angegebene Adresse aktualisiert.  
**Hinweis:** Nicht alle Provider unterstützen IPv6!

---

## Fehlerbehandlung & Tipps

- Existiert keine `config/config.yaml`, gibt der Container beim Start einen Fehler aus und beendet sich.
- Fehlerhafte Konfigurationen werden beim Start und bei jeder Änderung erkannt und mit einer klaren Fehlermeldung im Log ausgegeben.
- Die zuletzt bekannte IP wird in `/tmp/last_ip_v4.txt` und `/tmp/last_ip_v6.txt` gespeichert.

---

## Mitmachen & Support

Pull Requests und Verbesserungen sind willkommen!  
Bei Fragen oder Problemen bitte ein Issue auf GitHub eröffnen.

---

## Lizenz

MIT License

---

## Hinweis zur Entstehung

Dieses Projekt wurde mit Unterstützung von **GitHub Copilot** erstellt.  
Bei Fehlern oder Verbesserungsvorschlägen gerne ein Issue im Repository eröffnen!

---

## Logging-Konfiguration

Diese Anwendung unterstützt flexibles Logging sowohl auf der Konsole als auch in einer Logdatei. Du kannst die Ausführlichkeit (Loglevel) für beide Ausgaben unabhängig steuern und Logrotation für eine dauerhafte Speicherung aktivieren.

### Konfigurationsoptionen

Füge folgenden Abschnitt zu deiner `config.yaml` hinzu:

```yaml
# Logging-Konfiguration (optional)
logging:
  enabled: false                 # Auf true setzen, um Datei-Logging zu aktivieren
  file: "/app/config/dyndns.log" # Pfad zur Logdatei (Verzeichnis wird bei Bedarf erstellt)
  max_size_mb: 10                # Maximale Größe der Logdatei in MB, bevor rotiert wird
  backup_count: 3                # Anzahl der zu behaltenden Backup-Dateien

# Loglevel für Konsole und Datei
consolelevel: "INFO"   # Minimales Level für Nachrichten auf der Konsole
loglevel: "WARNING"    # Minimales Level für Nachrichten in der Logdatei
```

### Funktionsweise

- **Konsolen-Logging (`consolelevel`):** Alle Log-Meldungen ab diesem Level werden auf der Konsole (stdout) ausgegeben. Das ist besonders nützlich für die Live-Überwachung, z.B. mit `docker logs <container>`.
- **Datei-Logging (`loglevel`):** Wenn Datei-Logging aktiviert ist, werden nur Meldungen ab diesem Level in die Logdatei geschrieben. So bleiben deine Logdateien übersichtlich und enthalten nur wichtige Ereignisse.
- **Logrotation:** Wird die maximale Dateigröße (`max_size_mb`) erreicht, wird die Logdatei rotiert. Es werden so viele Backup-Dateien (`backup_count`) behalten, wie angegeben (z.B. `dyndns.log.1`, `dyndns.log.2`, ...).
- **Persistente Logs:** Wenn du `/app/config` als Docker-Volume mountest, bleiben deine Logs auch nach einem Container-Neustart erhalten.

### Hinweise

- Wenn der Abschnitt `logging` fehlt oder `enabled` auf `false` steht, ist nur das Konsolen-Logging aktiv.
- Die Logdatei wird automatisch erstellt, sobald die erste relevante Meldung geloggt wird.
- Die Logrotation verhindert, dass Logdateien unbegrenzt wachsen.
- Wenn `consolelevel` und `loglevel` nicht definiert sind, werden Standardwerte verwendet ("INFO" für Konsole, "WARNING" für Datei).

---

## Fehlerbehebung

### Häufige Probleme

1. **Container beendet sich sofort:**
   - Überprüfe, ob `config/config.yaml` existiert und gültig ist
   - Prüfe die Dateiberechtigungen (Container muss die Config lesen können)
   - Schau in die Docker-Logs: `docker logs <container-name>`

2. **Keine Logs sichtbar:**
   - Verwende `docker logs <container-name>` für die Konsolenausgabe
   - Stelle sicher, dass der Container läuft: `docker ps`
   - Für persistente Logs aktiviere das File-Logging in der Config

3. **Provider-Updates schlagen fehl:**
   - Überprüfe, ob API-Token/Credentials korrekt sind
   - Teste, ob die Provider-API erreichbar ist
   - Stelle sicher, dass Domain/Hostname im Provider-Dashboard existiert
   - Prüfe Rate-Limits - manche Provider haben strenge Beschränkungen

4. **Interface-Modus funktioniert nicht:**
   - Stelle sicher, dass Docker mit `network_mode: host` läuft
   - Überprüfe, ob der Interface-Name auf dem Host-System existiert
   - Prüfe, ob das Interface eine gültige IP-Adresse hat

5. **IPv6-Probleme:**
   - Nicht alle Provider unterstützen IPv6
   - Überprüfe, ob dein Netzwerk/ISP IPv6-Konnektivität bereitstellt
   - Link-lokale Adressen (fe80::) werden automatisch ausgeschlossen

6. **File-Logging funktioniert nicht:**
   - Prüfe, ob das Log-Verzeichnis beschreibbar ist
   - Stelle sicher, dass `logging.enabled` auf `true` steht
   - Überprüfe, ob der Log-Dateipfad im Container zugänglich ist

### Debug-Modus

Für detaillierte Fehlersuche setze das Loglevel auf DEBUG:

```yaml
consolelevel: "DEBUG"
loglevel: "DEBUG"
```

Dies zeigt detaillierte Informationen über:
- HTTP-Anfragen und -Antworten
- IP-Erkennungsprozess
- Provider-Authentifizierung
- Konfigurationsparsing
- **Benachrichtigungsverarbeitung** (warum Benachrichtigungen gesendet oder unterdrückt werden)
- **Cooldown-Status** für jeden Benachrichtigungsdienst
- **Service-Konfigurationsprüfungen** (aktiviert/deaktiviert, Level-Übereinstimmung, etc.)

---

## 🔄 Netzwerk-Resilienz

### Gelöstes Problem
Früher beendete sich der DynDNS-Client komplett, wenn er keine IP-Adresse ermitteln konnte, was zu folgenden Problemen führte:
- ❌ Keine Logs während Netzwerkausfällen
- ❌ Service-Unterbrechung mit manuellem Neustart
- ❌ Kompletter Ausfall bei DNS-Auflösungsproblemen

### Lösung: Resiliente Netzwerkbehandlung

Der erweiterte Client bietet nun **kugelsichere Netzwerk-Resilienz**:

#### 🌐 Mehrere IP-Erkennungsdienste
Anstatt sich auf einen einzigen Service zu verlassen, versucht der Client mehrere Services nacheinander:

**IPv4-Services:**
```yaml
ip_services:
  - "https://api.ipify.org"           # Primärer Service
  - "https://ifconfig.me/ip"          # Backup 1
  - "https://icanhazip.com"           # Backup 2  
  - "https://checkip.amazonaws.com"   # Backup 3
  - "https://ipecho.net/plain"        # Backup 4
  - "https://myexternalip.com/raw"    # Backup 5
```

**IPv6-Services:**
```yaml
ip6_services:
  - "https://api64.ipify.org"         # Primärer IPv6-Service
  - "https://ifconfig.me/ip"          # Backup 1 (unterstützt IPv6)
  - "https://icanhazip.com"           # Backup 2 (automatische IPv6-Erkennung)
  - "https://v6.ident.me"            # Backup 3 (IPv6-spezifisch)
  - "https://ipv6.icanhazip.com"     # Backup 4 (IPv6-spezifisch)
```

#### ⏱️ Intelligente Retry-Strategie
- **Erste Fehlschläge:** Wiederholung alle 60 Sekunden
- **Anhaltende Fehlschläge:** Exponentieller Backoff (60s → 120s → 240s → bis zu 10 Minuten)
- **Automatische Wiederherstellung:** Rückkehr zu normalen Intervallen wenn Netzwerk zurückkehrt

#### 🔧 Fallback-Mechanismen
1. **Mehrere externe Services:** Versucht 6 verschiedene IP-Erkennungsdienste
2. **Interface-Fallback:** Verwendet lokale Netzwerk-Interface-IP wenn alle externen Services fehlschlagen
3. **Graceful Degradation:** Läuft ohne Updates weiter bei komplettem Netzwerkausfall

#### 📊 Erweiterte Logs während Ausfällen

**Beispiel-Log-Ausgabe bei Netzwerkproblemen:**
```
2025-07-09 10:00:00 [INFO] NETWORK --> Versuche IP-Ermittlung über 6 Services...
2025-07-09 10:00:01 [WARNING] NETWORK --> ❌ Service https://api.ipify.org fehlgeschlagen: Name resolution error
2025-07-09 10:00:02 [INFO] NETWORK --> ✅ IP erfolgreich ermittelt von https://ifconfig.me/ip: 203.0.113.45
```

**Bei komplettem Netzwerkausfall:**
```
2025-07-09 10:05:00 [WARNING] NETWORK --> ❌ Alle IP-Services fehlgeschlagen
2025-07-09 10:05:00 [WARNING] NETWORK --> ⚠️ Keine IP verfügbar (Fehler #1). Warte 60s...
2025-07-09 10:05:00 [INFO] MAIN --> 🔄 Programm läuft weiter trotz Netzwerkproblemen...
```

**Netzwerk-Wiederherstellung:**
```
2025-07-09 10:10:00 [INFO] NETWORK --> ✅ IP erfolgreich ermittelt von https://api.ipify.org: 203.0.113.45
2025-07-09 10:10:00 [INFO] NETWORK --> ✅ Netzwerk wiederhergestellt nach 5 Fehlern
```

#### ⚙️ Konfigurationsoptionen

```yaml
# Netzwerk-Resilienz-Einstellungen
network_retry_interval: 60        # Wartezeit nach Fehlschlag (Sekunden)
max_failures_before_backoff: 5    # Fehlschläge vor exponentiellem Backoff
backoff_multiplier: 2.0           # Backoff-Multiplikator (2.0 = Verdopplung)
max_wait_time: 600                # Maximale Wartezeit (10 Minuten)
error_wait_time: 30               # Wartezeit nach unerwarteten Fehlern

# Interface-Fallback
enable_interface_fallback: true   # Interface-IP als Fallback verwenden
interface: "eth0"                  # Interface für Fallback-IP
```

#### 🎯 Vorteile

- **✅ 99.9% Uptime:** Service läuft auch bei Netzwerkproblemen weiter
- **✅ Automatische Wiederherstellung:** Keine manuelle Intervention nötig
- **✅ Ressourceneffizient:** Intelligenter Backoff verhindert Ressourcenverschwendung
- **✅ Detaillierte Überwachung:** Immer wissen was passiert
- **✅ Kein Datenverlust:** Kontinuierliche Logs auch während Ausfällen
- **✅ Production Ready:** Behandelt echte Netzwerk-Szenarien

---
