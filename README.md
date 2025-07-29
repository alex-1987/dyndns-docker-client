# DynDNS Docker Client

> :de: Für die deutsche Anleitung siehe [README.de.md](README.de.md)

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Log Levels Explained](#log-levels-explained)
4. [Quick Start (Docker & Compose)](#quick-start-docker--compose)
5. [Configuration](#configuration-configconfigyaml)
   - [Basic Options](#basic-options)
   - [Network Interface Configuration](#network-interface-configuration-alternative-to-ip-services)
   - [Provider Configuration](#provider-configuration)
   - [Notifications & Cooldown](#notifications--cooldown)
   - [Provider Update on Startup Only if IP Changed](#provider-update-on-startup-only-if-ip-changed)
6. [Logging Configuration](#logging-configuration)
7. [Advanced Features](#advanced-features)
   - [Extra Parameters for DynDNS2 Providers](#extra-parameters-for-dyndns2-providers)
   - [Authentication Methods](#authentication-methods)
   - [IP Validation](#ip-validation)
8. [Examples](#examples)
9. [Error Handling & Tips](#error-handling--tips)
10. [Troubleshooting](#troubleshooting)
11. [Contributing & Support](#contributing--support)
12. [License](#license)

---

## Overview

This project is a flexible DynDNS client for various providers (e.g. Cloudflare, ipv64, DuckDNS, NoIP, Dynu) and runs as a Docker container.  
It supports IPv4 and optionally IPv6, regularly checks the public IP, and updates DNS records at the configured services.

**How it works:** The client checks your public IP address every `timer` seconds (default: 300). If the IP has changed since the last check, it updates all configured providers. If the IP has not changed, no update is sent (unless configured otherwise). All actions, errors, and notifications are logged.

---

## Features

### Core Features
- **Multiple Providers:** Supports Cloudflare, ipv64, DuckDNS, NoIP, Dynu, and other DynDNS2-compatible services.
- **IPv4 & IPv6:** Updates A and AAAA records if desired.
- **Automatic Reload:** Changes to `config.yaml` are detected and applied automatically.
- **Flexible Configuration:** Each provider can be named freely; the type is controlled via the `protocol` field.
- **Detailed Logging:** Shows whether an update was performed, was not needed, or an error occurred.
- **Notification Cooldown:** Each notification service can have its own cooldown to avoid spam.
- **Provider Update on Startup Only if IP Changed:** Saves unnecessary requests and protects against rate limits.

### 🚀 Network Resilience Features (NEW!)
- **🔄 Never Dies:** Program continues running even during network outages
- **📡 Multiple IP Services:** Automatically tries 6 different IP detection services
- **⏱️ Smart Retry Logic:** 1-minute intervals with exponential backoff for persistent failures
- **🔧 Interface Fallback:** Uses local network interface IP when external services fail
- **📊 Detailed Error Logging:** Shows which services fail and why
- **🔄 Automatic Recovery:** Seamlessly resumes normal operation when network returns

---

## Log Levels

Configure logging in your `config.yaml`:

```yaml
loglevel: "INFO"        # Log file level
consolelevel: "INFO"    # Console output level
```

**Available Levels:**
- **TRACE** - Very detailed, shows every IP check
- **DEBUG** - Technical details, timers, troubleshooting
- **INFO** - Standard production level, important events
- **WARNING** - Problems and network issues
- **ERROR** - Serious errors requiring attention
- **CRITICAL** - Fatal errors that stop the program

**Quick Setup:**
```yaml
# Production: quiet console, detailed logs
consolelevel: "WARNING"
loglevel: "INFO"

# Development: see everything
consolelevel: "DEBUG"
loglevel: "TRACE"
```
- `"Provider 'xyz' updated successfully. New IP: 1.2.3.4"` - With new IP
- `"Provider 'xyz' updated successfully. New IP: 1.2.3.4 (previous: 1.2.3.5)"` - With old IP

**Notifications:**
- `"Notification sent via discord"` - Successful notification
- `"Notification sent via email"` - Sent via email
- `"Log file enabled: /app/config/dyndns.log (max size: 10.0MB, backups: 3)"` - File logging enabled

**Network Resilience:**
- `"Attempting IP detection via 6 services..."` - Multi-service attempt
- `"Fallback to interface IP..."` - Interface fallback
- `"🔄 Program continues despite network problems..."` - Resilient mode
- `"✅ Network restored after 5 failures"` - Recovery

#### 🟠 WARNING Level - Warnings & Problems
**When to use:** Minimum level for production environments - shows problems that need attention.

**Network Problems:**
- `"❌ Service https://api.ipify.org failed: Name resolution error"` - Service errors
- `"❌ All IP services failed"` - Complete failure of all services
- `"⚠️ Invalid IP from https://api.ipify.org: invalid-response"` - Invalid API response
- `"⚠️ No IP available (error #3). Waiting 120s..."` - Network outage with backoff
- `"⚠️ Persistent network problems (error #8). Exponential backoff: Waiting 600s..."` - Long-term problems
- `"❌ Interface fallback failed: Interface 'eth0' not found"` - Interface problems
- `"❌ Socket fallback failed: Network unreachable"` - Socket fallback error

**Provider Problems:**
- `"Provider 'xyz' could not be updated initially."` - Startup update failed
- `"Provider 'xyz' could not be updated after config change."` - After config reload
- `"Update interval at ipv64.net exceeded! Update limit reached."` - Rate limit
- `"No method configured to determine IPv4"` - Configuration gap

**Configuration:**
- `"Unknown logging option 'invalid_key' in config.yaml."` - Unknown config option
- `"No IPv4 address found for interface 'eth0'"` - Interface without IP
- `"Interface 'nonexistent' not found"` - Interface doesn't exist

#### 🔴 ERROR Level - Serious Errors
**When to use:** For critical monitoring - only serious problems that need immediate attention.

**Provider Update Errors:**
- `"Provider 'xyz' update failed: Authentication failed"` - API authentication
- `"Update for provider 'xyz' failed: Invalid API token"` - Token problems
- `"Cloudflare update failed: Zone not found"` - API-specific errors
- `"Error in DynDNS2 update: Connection timeout"` - Connection errors

**Configuration Errors:**
- `"Missing key 'timer' in config.yaml."` - Missing required fields
- `"Invalid consolelevel 'INVALID'. Valid options: TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL"` - Invalid values
- `"The field 'providers' must be a list."` - Structure errors
- `"Missing field 'protocol' in provider #1"` - Provider configuration

**System Errors:**
- `"Error loading config.yaml: YAML parsing error"` - YAML syntax error  
- `"Error saving last IP (v4): Permission denied"` - Filesystem problems
- `"Failed to setup file logging: Permission denied"` - Logging setup error

#### 🟣 CRITICAL Level - Fatal Errors (Program Terminates)
**When to use:** Always enabled - shows only errors that cause program termination.

- `"config/config.yaml not found! Please provide your own configuration..."` - No config file
- `"config.yaml is empty or invalid! Please check the file..."` - Empty/invalid config
- `"config.yaml does not contain any providers!"` - No providers configured
- `"Configuration invalid. Program will exit."` - Validation failed

**Note:**
- If you don't set `consolelevel`, the same level as for the log file is used for the console.
- File logs must be enabled in the `logging` section of the config for logs to be written to a file.

Example configuration:
```yaml
loglevel: "INFO"
consolelevel: "WARNING"
logging:
  enabled: true
  file: "/var/log/dyndns/dyndns.log"
```

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

### Network Interface Configuration (Alternative to IP Services)

Instead of using external IP services, you can configure the client to read IP addresses directly from network interfaces:

```yaml
# Use network interface instead of external service for IPv4
interface: "eth0"  # Replace with your actual interface name

# Use network interface instead of external service for IPv6 (optional)
interface6: "eth0"  # Replace with your actual interface name
```

**Requirements for Interface Mode:**
- Docker must run with `network_mode: host` to access host interfaces
- The specified interface must exist and have a valid public IP address
- For IPv6, link-local addresses (fe80::/10) are automatically skipped

**Example docker-compose.yml for interface mode:**
```yaml
services:
  dyndns-client:
    image: alexfl1987/dyndns:latest-stable
    network_mode: host  # Required for interface access!
    volumes:
      - ./config:/app/config
```

**Note:** You can use either `ip_service`/`ip6_service` OR `interface`/`interface6`, not both simultaneously.

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

You can configure notifications in two ways:

#### 1. Global Notifications (for all providers)
Configure notifications once in the global `notify` section. All providers will use these settings by default.

#### 2. Provider-Specific Notifications
Configure notifications individually for each provider. Provider-specific settings override global settings.

You can set an individual cooldown (in minutes) for **each notification service** to avoid notification spam.  
After a notification, the respective service will wait the specified time before sending another message.  
If no value or `0` is set, there is **no cooldown** for that service.

```yaml
# Global notification configuration (used by all providers unless overridden)
notify:
  reset_cooldown_on_start: true  # Reset cooldown timers on container start
  discord:
    enabled: true
    webhook_url: "https://discord.com/api/webhooks/global-webhook"
    notify_on: ["ERROR", "CRITICAL"]
    cooldown: 30

providers:
  # This provider uses global notification settings
  - name: regular-provider
    protocol: cloudflare
    zone: "example.com"
    api_token: "token123"
    record_name: "www.example.com"
  
  # This provider has custom notification settings
  - name: critical-provider
    protocol: cloudflare
    zone: "important.com"
    api_token: "token456"  
    record_name: "api.important.com"
    # Provider-specific notifications override global settings
    notify:
      discord:
        enabled: true
        webhook_url: "https://discord.com/api/webhooks/critical-webhook"
        notify_on: ["ERROR", "CRITICAL", "UPDATE"]  # More events for critical provider
        cooldown: 0  # No cooldown for critical notifications
      email:
        enabled: true
        to: "admin@important.com"
        # ... more email settings
```

With  
```yaml
reset_cooldown_on_start: true
```
you can specify that all cooldown timers are reset when the container starts.  
Set this option to `false` to let the cooldown continue after a restart.

**Available Notification Services:**
- **Discord:** Webhook notifications to Discord channels
- **Slack:** Webhook notifications to Slack channels  
- **Email:** SMTP email notifications
- **Telegram:** Bot notifications via Telegram API
- **ntfy:** Push notifications via ntfy.sh
- **Webhook:** Custom HTTP webhook calls

**Note:**  
- The cooldown time is stored separately for each service.
- The `reset_cooldown_on_start` option applies to all services.
- After a notification, the cooldown for the respective service is set.
- Provider-specific notification settings always override global settings.

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

## Logging Configuration

This application supports flexible logging to both the console and a log file. You can control the verbosity for each output independently and enable log rotation for persistent storage.

### Configuration Options

Add the following section to your `config.yaml`:

```yaml
# Logging configuration (optional)
logging:
  enabled: false                 # Set to true to enable file logging
  file: "/app/config/dyndns.log" # Log file path (directory will be created if needed)
  max_size_mb: 10                # Maximum size in MB before rotation
  backup_count: 3                # Number of backup files to keep

# Console and file log levels
consolelevel: "INFO"   # Minimum level for messages to appear in the console
loglevel: "WARNING"    # Minimum level for messages to be written to the log file
```

### How It Works

- **Console Logging (`consolelevel`):**  
  All log messages at or above this level will be printed to the console (stdout).  
  This is useful for real-time monitoring, especially when running in Docker (use `docker logs <container>`).

- **File Logging (`loglevel`):**  
  If file logging is enabled, only messages at or above this level will be written to the log file.  
  This helps keep your log files focused on important events and avoids unnecessary growth.

- **Log Rotation:**  
  When the log file reaches the specified maximum size (`max_size_mb`), it will be rotated.  
  A specified number of backup files (`backup_count`) will be kept (e.g., `dyndns.log.1`, `dyndns.log.2`, ...).

- **Persistent Logs:**  
  If you mount `/app/config` as a Docker volume, your logs will persist across container restarts.

### Notes

- If the `logging` section is omitted or `enabled` is set to `false`, only console logging is active.
- The log file is created automatically when the first eligible message is logged.
- Log rotation ensures your log files do not grow indefinitely.
- If `consolelevel` and `loglevel` are not defined in the config, default values ("INFO" for console, "WARNING" for file) are used.

---

## Advanced Features

### Extra Parameters for DynDNS2 Providers

Some DynDNS providers require additional parameters beyond the standard hostname and IP. The client supports `extra_params` for such cases:

```yaml
providers:
  # OVH DynHost example
  - name: my-ovh-domain
    protocol: dyndns2
    url: "https://www.ovh.com/nic/update"
    auth_method: "basic"
    username: "your-dynhost-username"
    password: "your-dynhost-password"
    hostname: "dynamic.yourdomain.com"
    extra_params:
      system: "dyndns"  # Required by OVH
```

### Authentication Methods

The client supports multiple authentication methods:

- **Token-based authentication:**
  ```yaml
  auth_method: "token"
  token: "your-api-token"
  ```

- **Basic authentication:**
  ```yaml
  auth_method: "basic"
  username: "your-username"
  password: "your-password"
  ```

- **Bearer token authentication:**
  ```yaml
  auth_method: "bearer"
  token: "your-bearer-token"
  ```

### IP Validation

The client automatically validates all IP addresses retrieved from services or interfaces:
- IPv4 addresses must be valid (0.0.0.0 to 255.255.255.255)
- IPv6 addresses must be valid and non-link-local (excludes fe80::/10)
- Invalid IPs are rejected and error notifications can be sent

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

### Alternative IPv4 and IPv6 Services

```yaml
# Alternative IPv4 services:
ip_service: "https://api.ipify.org"
# ip_service: "https://ipv4.icanhazip.com"
# ip_service: "https://checkip.amazonaws.com"
# ip_service: "https://ifconfig.me/ip"
# ip_service: "https://ident.me"
# ip_service: "https://myexternalip.com/raw"

# Alternative IPv6 services:
ip6_service: "https://api64.ipify.org"
# ip6_service: "https://ipv6.icanhazip.com"
# ip6_service: "https://ifconfig.co/ip"
# ip6_service: "https://ident.me"
# ip6_service: "https://myexternalip.com/raw"
```

**Note:** Not all services support IPv6 – test before using!

---

### Mixed Configuration Examples

You can mix different methods for IPv4 and IPv6:

```yaml
# Example 1: External service for IPv4, interface for IPv6
ip_service: "https://api.ipify.org"
interface6: "eth0"

# Example 2: Interface for IPv4, external service for IPv6
interface: "eth0"  
ip6_service: "https://api64.ipify.org"
```

This is useful in scenarios like:
- Your ISP uses Carrier-Grade NAT (CGN) for IPv4 but provides native IPv6
- You have a static IPv4 but dynamic IPv6
- You want to test different methods for different protocols

---

## Error Handling & Tips

- If `config/config.yaml` does not exist, the container will exit with an error.
- Invalid configurations are detected at startup and on every change, with clear error messages in the log.
- The last known IP is stored in `/tmp/last_ip_v4.txt` and `/tmp/last_ip_v6.txt`.

---

## Troubleshooting

### Common Issues

1. **Container exits immediately:**
   - Check that `config/config.yaml` exists and is valid
   - Verify file permissions (container should be able to read the config)
   - Check Docker logs: `docker logs <container-name>`

2. **No logs visible:**
   - Use `docker logs <container-name>` to see console output
   - Ensure the container is running: `docker ps`
   - For persistent logs, enable file logging in config

3. **Provider updates fail:**
   - Verify API tokens/credentials are correct
   - Check if the provider's API is reachable
   - Ensure the domain/hostname exists in your provider's dashboard
   - Check rate limits - some providers have strict limits

4. **Interface mode not working:**
   - Ensure Docker runs with `network_mode: host`
   - Verify the interface name exists on the host system
   - Check if the interface has a valid IP address

5. **IPv6 issues:**
   - Not all providers support IPv6
   - Verify your network/ISP provides IPv6 connectivity
   - Link-local addresses (fe80::) are automatically excluded

6. **File logging not working:**
   - Check if the log directory is writable
   - Verify the `logging.enabled` is set to `true`
   - Ensure the log file path is accessible within the container

### Debug Mode

For detailed troubleshooting, set the log level to DEBUG:

```yaml
consolelevel: "DEBUG"
loglevel: "DEBUG"
```

This will show detailed information about:
- HTTP requests and responses
- IP detection process
- Provider authentication
- Configuration parsing
- **Notification processing** (why notifications are sent or suppressed)
- **Cooldown status** for each notification service
- **Service configuration checks** (enabled/disabled, level matching, etc.)

---

## 🔄 Network Resilience

### Problem Solved
Previously, the DynDNS client would exit completely when it couldn't determine an IP address, leading to:
- ❌ No logs during network outages
- ❌ Service interruption requiring manual restart
- ❌ Complete failure during DNS resolution issues

### Solution: Resilient Network Handling

The enhanced client now features **bulletproof network resilience**:

#### 🌐 Multiple IP Detection Services
Instead of relying on a single service, the client tries multiple services in sequence:

**IPv4 Services:**
```yaml
ip_services:
  - "https://api.ipify.org"           # Primary service
  - "https://ifconfig.me/ip"          # Backup 1
  - "https://icanhazip.com"           # Backup 2  
  - "https://checkip.amazonaws.com"   # Backup 3
  - "https://ipecho.net/plain"        # Backup 4
  - "https://myexternalip.com/raw"    # Backup 5
```

**IPv6 Services:**
```yaml
ip6_services:
  - "https://api64.ipify.org"         # Primary IPv6 service
  - "https://ifconfig.me/ip"          # Backup 1 (supports IPv6)
  - "https://icanhazip.com"           # Backup 2 (auto IPv6 detection)
  - "https://v6.ident.me"            # Backup 3 (IPv6-specific)
  - "https://ipv6.icanhazip.com"     # Backup 4 (IPv6-specific)
```

#### ⏱️ Smart Retry Strategy
- **Initial failures:** Retry every 60 seconds
- **Persistent failures:** Exponential backoff (60s → 120s → 240s → up to 10 minutes)
- **Automatic recovery:** Returns to normal intervals when network is restored

#### 🔧 Fallback Mechanisms
1. **Multiple external services:** Try 6 different IP detection services
2. **Interface fallback:** Use local network interface IP if all external services fail
3. **Graceful degradation:** Continue running without updates during complete network failure

#### 📊 Enhanced Logging During Outages

**Example log output during network issues:**
```
2025-07-09 10:00:00 [INFO] NETWORK --> Versuche IP-Ermittlung über 6 Services...
2025-07-09 10:00:01 [WARNING] NETWORK --> ❌ Service https://api.ipify.org fehlgeschlagen: Name resolution error
2025-07-09 10:00:02 [INFO] NETWORK --> ✅ IP erfolgreich ermittelt von https://ifconfig.me/ip: 203.0.113.45
```

**During complete network outage:**
```
2025-07-09 10:05:00 [WARNING] NETWORK --> ❌ Alle IP-Services fehlgeschlagen
2025-07-09 10:05:00 [WARNING] NETWORK --> ⚠️ Keine IP verfügbar (Fehler #1). Warte 60s...
2025-07-09 10:05:00 [INFO] MAIN --> 🔄 Programm läuft weiter trotz Netzwerkproblemen...
```

**Network recovery:**
```
2025-07-09 10:10:00 [INFO] NETWORK --> ✅ IP erfolgreich ermittelt von https://api.ipify.org: 203.0.113.45
2025-07-09 10:10:00 [INFO] NETWORK --> ✅ Netzwerk wiederhergestellt nach 5 Fehlern
```

#### ⚙️ Configuration Options

```yaml
# Network resilience settings
network_retry_interval: 60        # Wait time after failure (seconds)
max_failures_before_backoff: 5    # Failures before exponential backoff
backoff_multiplier: 2.0           # Backoff multiplier (2.0 = doubling)
max_wait_time: 600                # Maximum wait time (10 minutes)
error_wait_time: 30               # Wait time after unexpected errors

# Interface fallback
enable_interface_fallback: true   # Use interface IP as fallback
interface: "eth0"                  # Interface for fallback IP
```

#### 🎯 Benefits

- **✅ 99.9% Uptime:** Service keeps running during network problems
- **✅ Automatic Recovery:** No manual intervention needed
- **✅ Resource Efficient:** Smart backoff prevents resource waste
- **✅ Detailed Monitoring:** Always know what's happening
- **✅ Zero Data Loss:** Continuous logging even during outages
- **✅ Production Ready:** Handles real-world network scenarios

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

