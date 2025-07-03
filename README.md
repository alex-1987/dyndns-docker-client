# DynDNS Docker Client

> :de: Für die deutsche Anleitung siehe [README.de.md](README.de.md)

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Loglevel & Consolelevel](#loglevel--consolelevel)
4. [Quick Start (Docker & Compose)](#quick-start-docker--compose)
5. [Configuration](#configuration-configconfigyaml)
   - [Basic Options](#basic-options)
   - [Provider Configuration](#provider-configuration)
   - [Notifications & Cooldown](#notifications--cooldown)
   - [Provider Update on Startup Only if IP Changed](#provider-update-on-startup-only-if-ip-changed)
6. [Examples](#examples)
7. [Error Handling & Tips](#error-handling--tips)
8. [Contributing & Support](#contributing--support)
9. [License](#license)

---

## Overview

This project is a flexible DynDNS client for various providers (e.g. Cloudflare, ipv64, DuckDNS, NoIP, Dynu) and runs as a Docker container.  
It supports IPv4 and optionally IPv6, regularly checks the public IP, and updates DNS records at the configured services.

**How it works:** The client checks your public IP address every `timer` seconds (default: 300). If the IP has changed since the last check, it updates all configured providers. If the IP has not changed, no update is sent (unless configured otherwise). All actions, errors, and notifications are logged.

---

## Features

- **Multiple Providers:** Supports Cloudflare, ipv64, DuckDNS, NoIP, Dynu, and other DynDNS2-compatible services.
- **IPv4 & IPv6:** Updates A and AAAA records if desired.
- **Automatic Reload:** Changes to `config.yaml` are detected and applied automatically.
- **Flexible Configuration:** Each provider can be named freely; the type is controlled via the `protocol` field.
- **Detailed Logging:** Shows whether an update was performed, was not needed, or an error occurred.
- **Notification Cooldown:** Each notification service can have its own cooldown to avoid spam.
- **Provider Update on Startup Only if IP Changed:** Saves unnecessary requests and protects against rate limits.

---

## Loglevel & Consolelevel

The loglevel controls the **verbosity of the application's logs** (file and/or console). You can set two levels:
- `loglevel`: Controls what is written to the log file (if file logging is enabled)
- `consolelevel`: Controls what is printed to the console (stdout)

Set these options in your `config.yaml`:

```yaml
loglevel: "INFO"        # File log level (if file logging is enabled)
consolelevel: "INFO"    # Console log level (what is printed to the terminal)
```

**What is included at each level:**
- `CRITICAL`: Only fatal errors that cause the program to exit (e.g. missing config, unrecoverable errors)
- `ERROR`: All errors, including failed provider updates, invalid IPs, notification failures, config errors
- `WARNING`: Warnings about non-fatal issues (e.g. provider could not be updated, no valid IP found, fallback used)
- `INFO`: All successful update attempts, config reloads, notification sends, and all of the above
- `DEBUG`: Detailed technical information, including all requests/responses, IP detection steps, provider payloads, and all of the above
- `TRACE`: Routine and very verbose messages (e.g. "IP unchanged", "Next run in ... seconds"). Use this level if you want to see every check and loop, but be aware it will make the log file much larger.

**Examples of what you see in the log:**
- Every IP check (every `timer` seconds)
- Every provider update attempt (success, no change, or failure)
- All errors and warnings
- All notifications sent (and failures)
- All config reloads and hot-reload events
- All startup and shutdown events
- With `TRACE`: Also all routine status messages (e.g. "IP unchanged", "Next run in ...")

**Note:**
- If you do not set `consolelevel`, the console output will use the same level as `loglevel`.
- File logging must be enabled in the `logging` section of your config to write logs to a file.

### Loglevels Overview

| Loglevel | Description |
|----------|-------------|
| TRACE    | Routine/status messages (e.g. "IP unchanged", "Next run in ..."). Only shown if TRACE is set. Use for regular status to avoid log bloat. |
| DEBUG    | Debugging information, more detailed than INFO. |
| INFO     | Normal operational messages. |
| WARNING  | Warnings, something unexpected but not fatal. |
| ERROR    | Errors that require attention. |
| CRITICAL | Critical errors, program will exit. |

### Example configuration for loglevel and consolelevel

```yaml
loglevel: TRACE         # File loglevel: logs everything including routine messages
consolelevel: INFO      # Console loglevel: only show important info and above
```

- `loglevel` controls what is written to the log file (if file logging is enabled).
- `consolelevel` controls what is printed to the console.
- Set either to `TRACE` to see routine/status messages (e.g. "IP unchanged", "Next run in ...").

---

## Quick Start (Docker & Compose)

### Official Image from Docker Hub

```sh
docker pull alexfl1987/dyndns:latest-stable
```

Start the container with your own configuration:

```sh
docker run -u 1000:1000 \
  -d --name dyndns-client \
  -v $(pwd)/config/config.yaml:/app/config/config.yaml \
  alexfl1987/dyndns:latest-stable
```

> **Note:**  
> If `config/config.yaml` does not exist, the container will exit with an error.

---

### Docker Compose Example

Create a `docker-compose.yml` file:

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

Start with:

```sh
docker compose up -d
```

---

## Configuration (`config/config.yaml`)

**IMPORTANT:**  
Create a `config.yaml` file in the `config` folder!  
The content should be based on the provided `config.example.yaml`.

### Basic Options

```yaml
timer: 300  # Interval in seconds for IP checks
ip_service: "https://api.ipify.org"  # Service to fetch public IPv4
ip6_service: "https://api64.ipify.org"  # (Optional) Service to fetch public IPv6
skip_update_on_startup: true  # See below!
```

### Provider Configuration

```yaml
providers:
  - name: duckdns
    protocol: dyndns2
    url: "https://www.duckdns.org/update"
    token: "your-duckdns-token"
    domain: "example"
  - name: my-cloudflare
    protocol: cloudflare
    zone: "yourdomain.tld"
    api_token: "your_cloudflare_api_token"
    record_name: "sub.domain.tld"
  # ...more providers, see config.example.yaml...
```

### Notifications & Cooldown

You can set an individual cooldown (in minutes) for **each notification service** to avoid notification spam.  
After a notification, the respective service will wait the specified time before sending another message.  
If no value or `0` is set, there is **no cooldown** for that service.

```yaml
notify:
  reset_cooldown_on_start: true  # Reset cooldown timers on container start
  ntfy:
    cooldown: 10
    enabled: true
    url: "https://ntfy.sh/your-topic"
    notify_on: ["ERROR", "CRITICAL"]
  discord:
    cooldown: 30
    enabled: true
    webhook_url: "https://discord.com/api/webhooks/..."
    notify_on: ["ERROR", "CRITICAL"]
  email:
    cooldown: 0  # No cooldown for email
    enabled: true
    # ...more settings...
```

With  
```yaml
reset_cooldown_on_start: true
```
you can specify that all cooldown timers are reset when the container starts.  
Set this option to `false` to let the cooldown continue after a restart.

**Note:**  
- The cooldown time is stored separately for each service.
- The `reset_cooldown_on_start` option applies to all services.
- After a notification, the cooldown for the respective service is set.

---

### Provider Update on Startup Only if IP Changed

With the option  
```yaml
skip_update_on_startup: true
```
in your `config.yaml`, provider updates are **only performed on container startup if the public IP has changed since the last run**.  
If the IP is unchanged, no unnecessary updates are made.  
If the option is set to `false` or missing, an update is always performed on startup—regardless of the IP.

The last known IP is stored in the container under `/tmp`.

**Note:**  
- This option helps avoid unnecessary update requests if the IP has not changed.
- Only works if the IP is fetched from an external service (like ipify).

---

## Examples

### Update only IPv4, only IPv6, or both

- **Only IPv4:**  
  ```yaml
  ip_service: "https://api.ipify.org"
  ```
- **Only IPv6:**  
  ```yaml
  ip6_service: "https://api64.ipify.org"
  ```
- **Both:**  
  ```yaml
  ip_service: "https://api.ipify.org"
  ip6_service: "https://api64.ipify.org"
  ```

If you omit one of the entries, only the specified address will be updated.  
**Note:** Not all providers support IPv6!

---

## Error Handling & Tips

- If `config/config.yaml` does not exist, the container will exit with an error.
- Invalid configurations are detected at startup and on every change, with clear error messages in the log.
- The last known IP is stored in `/tmp/last_ip_v4.txt` and `/tmp/last_ip_v6.txt`.

---

## Contributing & Support

Pull requests and improvements are welcome!  
For questions or issues, please open an issue on GitHub.

---

## License

MIT License

---

## About

This project was created with the help of **GitHub Copilot**.  
If you find bugs or have suggestions, please open an issue in the repository!

---

## Network Interface Configuration

This application supports retrieving IP addresses from local network interfaces instead of using external services. This can be useful when:

- You're in a network without internet access
- You have a dedicated public IPv4/IPv6 address assigned to an interface
- You want to avoid dependency on external IP services

### Requirements for Interface Mode

To use this feature with Docker, you must run the container with host network mode:

```yaml
# docker-compose.yml example
services:
  dyndns:
    image: alex-1987/dyndns-docker-client:latest
    network_mode: host  # This is required ONLY when using interface mode!
    volumes:
      - ./config:/app/config
```

