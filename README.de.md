# DynDNS Docker Client

> :gb: For the English documentation see [README.md](README.md)

---

## Inhaltsverzeichnis

1. [Überblick](#überblick)
2. [Features](#features)
3. [Schnellstart (Docker & Compose)](#schnellstart-docker--compose)
4. [Konfiguration](#konfiguration-configconfigyaml)
   - [Grundlegende Optionen](#grundlegende-optionen)
   - [Provider-Konfiguration](#provider-konfiguration)
   - [Benachrichtigungen & Cooldown](#benachrichtigungen--cooldown)
   - [Provider-Update beim Neustart nur bei IP-Änderung](#provider-update-beim-neustart-nur-bei-ip-änderung)
5. [Beispiele](#beispiele)
6. [Fehlerbehandlung & Tipps](#fehlerbehandlung--tipps)
7. [Mitmachen & Support](#mitmachen--support)
8. [Lizenz](#lizenz)

---

## Überblick

Dieses Projekt ist ein flexibler DynDNS-Client für verschiedene Provider (z.B. Cloudflare, ipv64, DuckDNS, NoIP, Dynu) und läuft als Docker-Container.  
Es unterstützt IPv4 und optional IPv6, prüft regelmäßig die öffentliche IP und aktualisiert die DNS-Einträge bei den konfigurierten Diensten.

---

## Features

- **Mehrere Provider:** Unterstützt Cloudflare, ipv64, DuckDNS, NoIP, Dynu und andere DynDNS2-kompatible Dienste.
- **IPv4 & IPv6:** Aktualisiert A- und AAAA-Records, wenn gewünscht.
- **Automatisches Nachladen:** Änderungen an der `config.yaml` werden automatisch erkannt und übernommen.
- **Flexible Konfiguration:** Jeder Provider kann beliebig benannt werden, der Typ wird über das Feld `protocol` gesteuert.
- **Detailliertes Logging:** Zeigt an, ob ein Update durchgeführt wurde, nicht nötig war oder ein Fehler auftrat.
- **Benachrichtigungs-Cooldown:** Jeder Dienst kann einen eigenen Cooldown für Benachrichtigungen erhalten.
- **Provider-Update beim Neustart nur bei IP-Änderung:** Spart unnötige Requests und schützt vor Rate-Limits.

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

Du kannst für **jeden Notification-Dienst** einen eigenen Cooldown (in Minuten) setzen, um Benachrichtigungs-Spam zu vermeiden.  
Nach einer Benachrichtigung wartet der jeweilige Dienst die angegebene Zeit, bevor wieder eine Nachricht gesendet wird.  
Ist kein Wert gesetzt oder `0`, gibt es **keinen Cooldown** für diesen Dienst.

```yaml
notify:
  reset_cooldown_on_start: true  # Cooldown-Zähler wird beim Start zurückgesetzt
  ntfy:
    cooldown: 10
    enabled: true
    url: "https://ntfy.sh/dein-topic"
    notify_on: ["ERROR", "CRITICAL"]
  discord:
    cooldown: 30
    enabled: true
    webhook_url: "https://discord.com/api/webhooks/..."
    notify_on: ["ERROR", "CRITICAL"]
  email:
    cooldown: 0  # Kein Cooldown für E-Mail
    enabled: true
    # ...weitere Einstellungen...
```

Mit  
```yaml
reset_cooldown_on_start: true
```
kannst du festlegen, dass beim Start des Containers alle Cooldown-Zähler zurückgesetzt werden.  
Setze diese Option auf `false`, um den Cooldown auch nach einem Neustart weiterlaufen zu lassen.

**Hinweis:**  
- Die Cooldown-Zeit wird pro Dienst separat gespeichert.
- Die Option `reset_cooldown_on_start` gilt für alle Dienste gemeinsam.
- Nach einer Benachrichtigung wird der Cooldown für den jeweiligen Dienst gesetzt.

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
