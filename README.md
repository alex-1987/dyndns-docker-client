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

- **Multiple Providers:** Supports Cloudflare, ipv64, DuckDNS, NoIP, Dynu, and other DynDNS2-compatible services.
- **IPv4 & IPv6:** Updates A and AAAA records if desired.
- **Automatic Reload:** Changes to `config.yaml` are detected and applied automatically.
- **Flexible Configuration:** Each provider can be named freely; the type is controlled via the `protocol` field.
- **Detailed Logging:** Shows whether an update was performed, was not needed, or an error occurred.
- **Notification Cooldown:** Each notification service can have its own cooldown to avoid spam.
- **Provider Update on Startup Only if IP Changed:** Saves unnecessary requests and protects against rate limits.

---

### Log Levels Explained

- **DEBUG:**  
  Shows very detailed information for troubleshooting and development.  
  Examples: Internal variable values, function calls, processing steps.

- **INFO:**  
  Shows general information about normal application operation.  
  Examples: Successful updates, detected IP addresses, startup messages.

- **WARNING:**  
  Indicates something unexpected happened, but the application can continue running.  
  Examples: Temporary network issues, missing optional configuration, retry attempts.

- **ERROR:**  
  Indicates a serious problem that prevented an operation from completing.  
  Examples: Failed DNS update, permanent network failure, invalid configuration.

- **CRITICAL:**  
  Indicates a very severe error that may cause the application to stop or lose important functionality.  
  Examples: Fatal configuration errors, unhandled exceptions, application shutdown.

**Note:**  
The lower the log level (e.g. DEBUG), the more details are shown.  
For normal operation, INFO or WARNING is usually sufficient.  
Use DEBUG only for troubleshooting.

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

