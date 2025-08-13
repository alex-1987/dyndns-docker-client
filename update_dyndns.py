import sys
import os
import time
import requests
import yaml
import logging
import struct
import datetime
import socket
import subprocess
import re
import array
import tempfile
import ipaddress
from notify import send_notifications
from logging.handlers import RotatingFileHandler
from abc import ABC, abstractmethod

try:
    import fcntl
except ImportError:
    fcntl = None  # Windows doesn't have fcntl

print("DYNDNS CLIENT STARTUP")

class DynDNSState:
    """Zentrale Zustandsverwaltung für DynDNS Client."""
    
    def __init__(self):
        self.config = None
        self.log_level = "INFO"
        self.console_level = "INFO"
        self.file_logger = None
        
        # IP-Tracking
        self.last_ipv4 = None
        self.last_ipv6 = None
        
        # Netzwerk-Zustand
        self.resilient_mode = False
        self.failed_providers = []
        self.error_count = 0
        self.last_error_time = 0
        self.backoff_delay = 60
    
    def reset_network_state(self):
        """Setzt Netzwerk-Fehler-Zustand zurück."""
        self.resilient_mode = False
        self.failed_providers = []
        self.error_count = 0
    
    def add_failed_provider(self, provider_name):
        """Fügt einen fehlgeschlagenen Provider hinzu."""
        if provider_name not in self.failed_providers:
            self.failed_providers.append(provider_name)

# Globale Instanz
state = DynDNSState()

# Backward compatibility: Keep global references for existing code
config = None  # global, so update_provider can access it
log_level = "INFO"         # For file logging
console_level = "INFO"     # For console output
file_logger_instance = None

# Add a custom loglevel for very verbose, routine messages
CUSTOM_LEVELS = ["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# Add custom TRACE loglevel (lower than DEBUG)
TRACE_LEVEL_NUM = 5
logging.addLevelName(TRACE_LEVEL_NUM, "TRACE")

def trace(self, message, *args, **kws):
    if self.isEnabledFor(TRACE_LEVEL_NUM):
        self._log(TRACE_LEVEL_NUM, message, args, **kws)
logging.Logger.trace = trace

def setup_logging(loglevel, config=None):
    """
    Configures logging with the specified level.
    Enhanced to support file logging if configured.
    
    Args:
        loglevel: Log level as string (e.g. "INFO", "DEBUG")
        config: Optional configuration dictionary for file logging
    """
    global log_level, file_logger_instance
    state.log_level = loglevel
    log_level = loglevel
    
    # Only setup file logging if explicitly enabled
    if config and config.get("logging", {}).get("enabled", False):
        try:
            log_config = config["logging"]
            log_file = log_config.get("file", "/var/log/dyndns/dyndns.log")
            max_size = log_config.get("max_size_mb", 10) * 1024 * 1024
            backup_count = log_config.get("backup_count", 3)
            
            # Validate configuration values
            if max_size <= 0:
                raise ValueError("max_size_mb must be greater than 0")
            if backup_count < 0:
                raise ValueError("backup_count must be 0 or greater")
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            # Setup file handler
            file_handler = RotatingFileHandler(log_file, maxBytes=max_size, backupCount=backup_count)
            formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
            file_handler.setFormatter(formatter)
            
            # Create file logger
            file_logger_instance = logging.getLogger("dyndns_file")
            file_logger_instance.setLevel(TRACE_LEVEL_NUM if loglevel == "TRACE" else getattr(logging, loglevel))
            file_logger_instance.handlers = []  # Clear any existing handlers
            file_logger_instance.addHandler(file_handler)
            file_logger_instance.propagate = False
            
            # Update state
            state.file_logger = file_logger_instance
            
            # Log initial message to file
            start_msg = f"Log file enabled: {log_file} (max size: {max_size/1024/1024:.1f}MB, backups: {backup_count})"
            file_logger_instance.info(start_msg)
            print(f"{datetime.datetime.now(datetime.timezone.utc).isoformat()} [INFO] LOGGING --> {start_msg}")
            
        except Exception as e:
            print(f"{datetime.datetime.now(datetime.timezone.utc).isoformat()} [ERROR] LOGGING --> Failed to setup file logging: {e}")
            file_logger_instance = None
            state.file_logger = None
    else:
        file_logger_instance = None
        state.file_logger = None
    
    return loglevel

def log(message, level="INFO", section="MAIN", file_only_on_change=False):
    """
    Log a message with the specified level and section.
    Always logs to console, additionally logs to file if configured.
    
    Args:
        message: The message to log
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        section: Section/component name for the log
        file_only_on_change: If True, only log to file for ERROR/CRITICAL levels
    """
    global console_level, log_level, file_logger_instance
    
    # Get log levels with defaults - use state if available, otherwise globals
    current_console_level = state.console_level if hasattr(state, 'console_level') else globals().get('console_level', 'INFO')
    current_file_level = state.log_level if hasattr(state, 'log_level') else globals().get('log_level', 'INFO')
    
    # Log levels for filtering
    levels = ["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    try:
        message_idx = levels.index(level)
        console_idx = levels.index(current_console_level)
        should_log_console = message_idx >= console_idx
    except ValueError:
        should_log_console = True
    
    # Always log to console if level permits
    if should_log_console:
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        print(f"{timestamp} [{level}] {section} --> {message}")
    
    # Additionally log to file if configured
    current_file_logger = state.file_logger if hasattr(state, 'file_logger') and state.file_logger else file_logger_instance
    if current_file_logger is not None:
        # Check if we should log to file
        should_log_file = True
        if file_only_on_change and level not in ("ERROR", "CRITICAL"):
            should_log_file = False
        
        # Check file log level
        try:
            file_idx = levels.index(current_file_level)
            if message_idx < file_idx:
                should_log_file = False
        except ValueError:
            pass
        
        if should_log_file:
            file_message = f"{section} --> {message}"
            log_method = getattr(current_file_logger, level.lower(), current_file_logger.info)
            log_method(file_message)

def should_log(level, configured_level):
    """
    Determine if a message should be logged based on its level and the configured level.
    This replicates your existing logic for log filtering.
    Supports custom TRACE loglevel.
    """
    levels = ["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    try:
        message_idx = levels.index(level.upper())
        config_idx = levels.index(configured_level.upper())
        return message_idx >= config_idx
    except ValueError:
        return True  # If level not recognized, log it anyway

# Call this function in main() after loading the config
def initialize_logging(config):
    """Initialize the logging system based on configuration."""
    global _use_python_logging
    
    if config and "logging" in config and config["logging"].get("enabled", False):
        setup_logging(config)
        _use_python_logging = True
    # Otherwise, stick with the default print-based logging

def get_public_ip(ip_service):
    """
    Fetches the public IPv4 address from the given service.
    Now includes validation to ensure the result is actually an IPv4 address.
    """
    try:
        response = requests.get(ip_service, timeout=10)
        response.raise_for_status()
        ip = response.text.strip()
        
        # Validate that it's actually an IPv4 address
        if validate_ipv4(ip):
            return ip
        else:
            log(f"Service {ip_service} returned invalid IPv4 format: {ip}", "ERROR", section="IPV4")
            return None
    except Exception as e:
        log(f"Error fetching public IP: {e}", "ERROR")
        return None

def get_public_ipv6(ip_service="https://api64.ipify.org"):
    """
    Fetches the public IPv6 address from the given service.
    Now includes validation to ensure the result is actually an IPv6 address.
    """
    try:
        response = requests.get(ip_service, timeout=10)
        response.raise_for_status()
        ip6 = response.text.strip()
        
        # Validate that it's actually an IPv6 address
        if validate_ipv6(ip6):
            return ip6
        else:
            log(f"Service {ip_service} returned invalid IPv6 format: {ip6}", "ERROR", section="IPV6")
            return None
    except Exception as e:
        log(f"Error fetching public IPv6: {e}", "ERROR")
        return None

def get_cloudflare_zone_id(api_token, zone_name):
    """
    Retrieves the zone ID for a Cloudflare zone by name.
    """
    url = f"https://api.cloudflare.com/client/v4/zones?name={zone_name}"
    headers = {"Authorization": f"Bearer {api_token}"}
    resp = requests.get(url, headers=headers)
    data = resp.json()
    if data.get("success") and data["result"]:
        return data["result"][0]["id"]
    raise Exception(f"Zone ID for {zone_name} not found: {data}")

def get_cloudflare_record_id(api_token, zone_id, record_name):
    """
    Retrieves the record ID for a DNS record in a Cloudflare zone.
    """
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?name={record_name}"
    headers = {"Authorization": f"Bearer {api_token}"}
    resp = requests.get(url, headers=headers)
    data = resp.json()
    if data.get("success") and data["result"]:
        return data["result"][0]["id"]
    raise Exception(f"DNS record ID for {record_name} not found: {data}")

# =============================================================================
# UNIFIED PROVIDER ARCHITECTURE
# =============================================================================

from abc import ABC, abstractmethod

class BaseProvider(ABC):
    """Basis-Klasse für alle DynDNS-Provider."""
    
    def __init__(self, config):
        self.config = config
        self.name = config.get('name', 'unknown')
        # Support both 'type' and 'protocol' for backward compatibility
        self.provider_type = config.get('type', config.get('protocol', 'unknown'))
    
    def update_unified(self, current_ip, current_ip6):
        """Hauptupdate-Methode mit einheitlicher Logik."""
        log(f"BaseProvider: Starting unified update for {self.name}", "DEBUG", "PROVIDER")
        try:
            # Validierung
            self.validate_config()
            
            # Provider-spezifisches Update
            result = self.perform_update(current_ip, current_ip6)
            log(f"BaseProvider: Update result for {self.name}: {result}", "DEBUG", "PROVIDER")
            
            # Benachrichtigungen senden
            if result and result != "nochg":
                self.send_success_notification(current_ip or current_ip6)
                log(f"Provider '{self.name}' updated successfully.", "INFO", self.provider_type.upper())
            elif result == "nochg":
                log(f"Provider '{self.name}' - no change needed.", "TRACE", self.provider_type.upper())
            
            return result
            
        except Exception as e:
            log(f"BaseProvider: Exception in unified update for {self.name}: {str(e)}", "DEBUG", "PROVIDER")
            self.send_error_notification(str(e))
            log(f"Provider '{self.name}' update failed: {str(e)}", "ERROR", self.provider_type.upper())
            return False
    
    @abstractmethod
    def perform_update(self, current_ip, current_ip6):
        """Provider-spezifische Update-Logik."""
        pass
    
    @abstractmethod
    def validate_config(self):
        """Provider-spezifische Konfigurationsvalidierung."""
        pass
    
    def send_success_notification(self, ip):
        """Sendet Erfolgs-Benachrichtigung mit Fallback auf globale Konfiguration."""
        log(f"BaseProvider: Sending success notification for {self.name}", "DEBUG", "PROVIDER")
        msg = f"Provider '{self.name}' updated successfully. New IP: {ip}"
        
        # Provider-spezifische notify-Konfiguration verwenden, falls vorhanden
        notify_config = self.config.get("notify")
        
        # Fallback auf globale notify-Konfiguration wenn keine provider-spezifische vorhanden
        if not notify_config and state.config:
            notify_config = state.config.get("notify")
            log(f"BaseProvider: Using global notify config for {self.name}", "DEBUG", "PROVIDER")
        else:
            log(f"BaseProvider: Using provider-specific notify config for {self.name}", "DEBUG", "PROVIDER")
        
        send_notifications(notify_config, "UPDATE", msg, 
                         subject=f"🟢 **{self.name}** wurde erfolgreich aktualisiert!",
                         service_name=self.name)
    
    def send_error_notification(self, error):
        """Sendet Fehler-Benachrichtigung mit Fallback auf globale Konfiguration."""
        log(f"BaseProvider: Sending error notification for {self.name}", "DEBUG", "PROVIDER")
        msg = f"Provider '{self.name}' update failed: {error}"
        
        # Provider-spezifische notify-Konfiguration verwenden, falls vorhanden
        notify_config = self.config.get("notify")
        
        # Fallback auf globale notify-Konfiguration wenn keine provider-spezifische vorhanden
        if not notify_config and state.config:
            notify_config = state.config.get("notify")
            log(f"BaseProvider: Using global notify config for {self.name}", "DEBUG", "PROVIDER")
        else:
            log(f"BaseProvider: Using provider-specific notify config for {self.name}", "DEBUG", "PROVIDER")
        
        send_notifications(notify_config, "ERROR", msg,
                         subject=f"🔴 **{self.name}** Update fehlgeschlagen!",
                         service_name=self.name)

class CloudflareProvider(BaseProvider):
    """Cloudflare-spezifische Implementierung."""
    
    def __init__(self, config):
        super().__init__(config)
        # Validate configuration during initialization
        self.validate_config()
    
    def validate_config(self):
        # Support both 'api_token' and 'token' field names
        has_token = self.config.get('api_token') or self.config.get('token')
        if not has_token:
            raise ValueError("Missing Cloudflare config: need 'api_token' or 'token' field")
        
        required = ['zone', 'record_name']
        missing = [f for f in required if not self.config.get(f)]
        if missing:
            raise ValueError(f"Missing Cloudflare config: {missing}")
    
    def perform_update(self, current_ip, current_ip6):
        """Führt Cloudflare-Update durch."""
        # Delegiere an bestehende Funktion für Kompatibilität
        return update_cloudflare(self.config, current_ip, current_ip6)

class IPV64Provider(BaseProvider):
    """IPV64-spezifische Implementierung."""
    
    def __init__(self, config):
        super().__init__(config)
        # Validate configuration during initialization
        self.validate_config()
    
    def validate_config(self):
        required = ['token']
        missing = [f for f in required if not self.config.get(f)]
        if missing:
            raise ValueError(f"Missing IPV64 config: {missing}")
        
        # Domain/host/hostname validation
        if not any(k in self.config for k in ['domain', 'host', 'hostname']):
            raise ValueError("Missing IPV64 domain config: need 'domain', 'host', or 'hostname'")
    
    def perform_update(self, current_ip, current_ip6):
        """Führt IPV64-Update durch."""
        # Delegiere an bestehende Funktion für Kompatibilität
        return update_ipv64(self.config, current_ip, current_ip6)

class DynDNS2Provider(BaseProvider):
    """DynDNS2-spezifische Implementierung."""
    
    def __init__(self, config):
        super().__init__(config)
        # Validate configuration during initialization
        self.validate_config()
    
    def validate_config(self):
        required = ['url']
        missing = [f for f in required if not self.config.get(f)]
        if missing:
            raise ValueError(f"Missing DynDNS2 config: {missing}")
        
        # Hostname validation
        if not any(k in self.config for k in ['hostname', 'domain', 'host']):
            raise ValueError("Missing DynDNS2 hostname config: need 'hostname', 'domain', or 'host'")
        
        # Auth validation
        auth_method = self.config.get('auth_method', 'token')
        if auth_method in ['token', 'basic', 'bearer']:
            if not self.config.get('token') and not (self.config.get('username') and self.config.get('password')):
                raise ValueError("Missing DynDNS2 authentication: need 'token' or 'username'+'password'")
    
    def perform_update(self, current_ip, current_ip6):
        """Führt DynDNS2-Update durch."""
        # Delegiere an bestehende Funktion für Kompatibilität
        return update_dyndns2(self.config, current_ip, current_ip6)

# Provider-Factory
def create_provider(provider_config):
    """Erstellt Provider-Instanz basierend auf Typ."""
    # Support both 'type' and 'protocol' for backward compatibility
    provider_type = provider_config.get('type', provider_config.get('protocol', '')).lower()
    
    if not provider_type:
        available_types = 'cloudflare, ipv64, dyndns2'
        raise ValueError(f"No provider type specified. Available types: {available_types}")
    
    providers = {
        'cloudflare': CloudflareProvider,
        'ipv64': IPV64Provider,
        'dyndns2': DynDNS2Provider
    }
    
    provider_class = providers.get(provider_type)
    if not provider_class:
        available_types = ', '.join(providers.keys())
        raise ValueError(f"Unknown provider type: '{provider_type}'. Available types: {available_types}")
    
    return provider_class(provider_config)

# =============================================================================
# LEGACY PROVIDER FUNCTIONS (maintained for compatibility)
# =============================================================================

def update_cloudflare(provider, ip, ip6=None):
    """
    Updates an A and optionally AAAA record at Cloudflare if the IP has changed.
    Returns "updated", "nochg" or False.
    """
    api_token = provider['api_token']
    zone = provider['zone']
    record_name = provider['record_name']
    zone_id = get_cloudflare_zone_id(api_token, zone)
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    updated = False
    nochg = True

    # --- IPv4 (A-Record) ---
    if ip:
        url_a = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?name={record_name}&type=A"
        resp_a = requests.get(url_a, headers=headers)
        data_a = resp_a.json()
        log(f"Cloudflare GET A response: {data_a}", "DEBUG", section="CLOUDFLARE")
        if data_a.get("success") and data_a["result"]:
            record_a = data_a["result"][0]
            if record_a["content"] == ip:
                log(f"No update needed (IPv4 already set: {ip}).", "TRACE", section="CLOUDFLARE")
            else:
                url_patch = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_a['id']}"
                data_patch = {
                    "type": "A",
                    "name": record_name,
                    "content": ip
                }
                resp_patch = requests.patch(url_patch, json=data_patch, headers=headers)
                log(f"Cloudflare PATCH A response: {resp_patch.text}", "DEBUG", section="CLOUDFLARE")
                if resp_patch.ok:
                    updated = True
                    nochg = False
        else:
            log(f"A record {record_name} not found or error: {data_a}", "ERROR", section="CLOUDFLARE")
            nochg = False

    # --- IPv6 (AAAA-Record) ---
    if ip6:
        url_aaaa = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?name={record_name}&type=AAAA"
        resp_aaaa = requests.get(url_aaaa, headers=headers)
        data_aaaa = resp_aaaa.json()
        log(f"Cloudflare GET AAAA response: {data_aaaa}", "DEBUG", section="CLOUDFLARE")
        if data_aaaa.get("success") and data_aaaa["result"]:
            record_aaaa = data_aaaa["result"][0]
            if record_aaaa["content"] == ip6:
                log(f"No update needed (IPv6 already set: {ip6}).", "TRACE", section="CLOUDFLARE")
            else:
                url_patch = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_aaaa['id']}"
                data_patch = {
                    "type": "AAAA",
                    "name": record_name,
                    "content": ip6
                }
                resp_patch = requests.patch(url_patch, json=data_patch, headers=headers)
                log(f"Cloudflare PATCH AAAA response: {resp_patch.text}", section="CLOUDFLARE")
                if resp_patch.ok:
                    updated = True
                    nochg = False
        else:
            log(f"AAAA record {record_name} not found or error: {data_aaaa}", "ERROR", section="CLOUDFLARE")
            nochg = False

    if updated:
        return "updated"
    if nochg:
        return "nochg"
    return False

def update_ipv64(provider, ip, ip6=None):
    """
    Updates a record at ipv64.net.
    Supports IPv4 and IPv6.
    Returns "updated", "nochg" or False.
    The URL is hardcoded.
    """
    url = "https://ipv64.net/nic/update"
    params = {}
    if 'domain' in provider:
        params['domain'] = provider['domain']
    elif 'host' in provider:
        params['host'] = provider['host']
    auth = None
    headers = {}
    auth_method = provider.get('auth_method', 'token')
    token = provider.get('token')
    if auth_method == "token":
        params['key'] = token
    elif auth_method == "basic":
        auth = ('none', token)
    elif auth_method == "bearer":
        headers['Authorization'] = f"Bearer {token}"
    if ip:
        params['ip'] = ip
    if ip6:
        params['ip6'] = ip6
    response = requests.get(url, params=params, auth=auth, headers=headers)
    log(f"ipv64 response: {response.text}", section="IPV64")
    resp_text = response.text.lower().strip()
    if "overcommited" in resp_text or response.status_code == 403:
        log("Update interval at ipv64.net exceeded! Update limit reached.", "ERROR", section="IPV64")
        return False
    if "nochg" in resp_text or "no change" in resp_text:
        log("No update needed (nochg).", "TRACE", section="IPV64")
        return "nochg"
    if "good" in resp_text or "success" in resp_text:
        return "updated"
    log(f"ipv64 update failed: {response.text}", "ERROR", section="IPV64")
    return False

def update_dyndns2(provider, ip, ip6=None):
    """
    Updates a DynDNS2-compatible service.
    Returns "updated", "nochg", or None on error.
    Now supports extra_params for services like OVH.
    """
    try:
        # Prepare URL and auth
        url = provider.get("url")
        params = {}
        
        # Determine hostname parameter (some providers use different names)
        hostname_param = None
        if "hostname" in provider:
            hostname_param = provider["hostname"]
        elif "domain" in provider:
            hostname_param = provider["domain"]
        elif "host" in provider:
            hostname_param = provider["host"]
            
        if not hostname_param:
            log(f"No hostname/domain/host specified in provider {provider.get('name')}", "ERROR", section="DYNDNS2")
            return None
            
        # Set basic parameters
        params["hostname"] = hostname_param
        if ip:
            params["myip"] = ip
        if ip6:
            params["myipv6"] = ip6
            
        # Add extra parameters (new feature)
        if "extra_params" in provider and isinstance(provider["extra_params"], dict):
            extra_params = provider["extra_params"]
            for key, value in extra_params.items():
                params[key] = value
                
        # Authentication
        auth = None
        headers = {}
        auth_method = provider.get("auth_method", "token")
        
        if auth_method == "token" and "token" in provider:
            params["hostname"] = f"{hostname_param}"
            params["token"] = provider["token"]
        elif auth_method == "basic" and "username" in provider and "password" in provider:
            auth = (provider["username"], provider["password"])
        elif auth_method == "bearer" and "token" in provider:
            headers["Authorization"] = f"Bearer {provider['token']}"
        else:
            log(f"Invalid or incomplete auth configuration in provider {provider.get('name')}", "ERROR", section="DYNDNS2")
            return None
            
        # Make the request
        response = requests.get(url, params=params, auth=auth, headers=headers, timeout=10)
        response_text = response.text.strip()
        
        # Log the response for debugging
        provider_name = provider.get("name", "unknown")
        log(f"[{provider_name}] response: {response_text}", "INFO", section="DYNDNS2")
        
        # Check for success or no change
        if "good" in response_text or "updated" in response_text or "update succeed" in response_text or "success" in response_text:
            return "updated"
        elif "nochg" in response_text or "nochange" in response_text:
            log(f"[{provider_name}] No update needed (nochg).", "TRACE", section="DYNDNS2")
            return "nochg"
        else:
            log(f"[{provider_name}] update failed: {response_text}", "ERROR", section="DYNDNS2")
            return None
            
    except Exception as e:
        log(f"Error in DynDNS2 update: {e}", "ERROR", section="DYNDNS2")
        return None

def validate_config(config):
    """
    Checks config.yaml for required fields and prints errors with line numbers.
    Returns True if everything is fine, otherwise False.
    """
    required_top = ["timer", "providers"]
    allowed_protocols = ("cloudflare", "ipv64", "dyndns2")
    
    for key in required_top:
        if key not in config:
            log(f"Missing key '{key}' in config.yaml.", "ERROR")
            return False
    
    # Validate logging configuration if present
    if "logging" in config:
        logging_config = config["logging"]
        if not isinstance(logging_config, dict):
            log("The field 'logging' must be a dictionary.", "ERROR")
            return False
        
        # Check for valid logging options
        valid_logging_keys = ["enabled", "file", "max_size_mb", "backup_count"]
        for key in logging_config:
            if key not in valid_logging_keys:
                log(f"Unknown logging option '{key}' in config.yaml.", "WARNING")
        
        # Validate file path if logging is enabled
        if logging_config.get("enabled", False):
            if "file" not in logging_config:
                log("Missing 'file' option in logging configuration when enabled=true.", "ERROR")
                return False
    
    # Validate log levels
    valid_levels = ["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if "consolelevel" in config and config["consolelevel"] not in valid_levels:
        log(f"Invalid consolelevel '{config['consolelevel']}'. Valid options: {', '.join(valid_levels)}", "ERROR")
        return False
    
    if "loglevel" in config and config["loglevel"] not in valid_levels:
        log(f"Invalid loglevel '{config['loglevel']}'. Valid options: {', '.join(valid_levels)}", "ERROR")
        return False
    
    if not isinstance(config["providers"], list):
        log("The field 'providers' must be a list.", "ERROR")
        return False
    for idx, provider in enumerate(config["providers"]):
        if "protocol" not in provider:
            log(f"Missing field 'protocol' in provider #{idx+1} ({provider.get('name','?')}) in config.yaml.", "ERROR")
            return False
        if provider["protocol"] not in allowed_protocols:
            log(
                f"Invalid field 'protocol' ('{provider['protocol']}') in provider #{idx+1} ({provider.get('name','?')}) in config.yaml. "
                f"Allowed: {', '.join(allowed_protocols)}.",
                "ERROR"
            )
            return False
        if "url" not in provider and provider["protocol"] not in ("cloudflare", "ipv64"):
            log(f"Missing field 'url' in provider #{idx+1} ({provider.get('name','?')}) in config.yaml.", "ERROR")
            return False
        if provider["protocol"] == "cloudflare":
            for field in ("zone", "api_token", "record_name"):
                if field not in provider:
                    log(f"Missing field '{field}' in Cloudflare provider #{idx+1} ({provider.get('name','?')}) in config.yaml.", "ERROR")
                    return False
    return True

def _ip_cache_file(ip_version):
    return f"/tmp/last_ip_{ip_version}.txt"

def load_last_ip(ip_version):
    try:
        with open(_ip_cache_file(ip_version), "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def save_last_ip(ip_version, ip):
    try:
        with open(_ip_cache_file(ip_version), "w") as f:
            f.write(str(ip) if ip is not None else "")
    except Exception as e:
        log(f"Error saving last IP ({ip_version}): {e}", "ERROR", section="MAIN")

def update_provider(provider, ip, ip6=None, log_success_if_nochg=True, old_ip=None, old_ip6=None):
    """
    Selects the appropriate update function for the provider based on the protocol/type.
    Now supports both unified provider architecture and legacy protocol-based approach.
    Logs the result and returns True (update/nochg) or False (error).
    """
    try:
        provider_name = provider.get("name", "PROVIDER")
        protocol = provider.get("protocol", provider.get("type", "unknown"))
        
        # Try unified provider architecture first
        if protocol in ['cloudflare', 'ipv64', 'dyndns2']:
            try:
                unified_provider = create_provider(provider)
                result = unified_provider.update_unified(ip, ip6)
                
                # Return boolean for compatibility
                if result == "updated":
                    return True
                elif result == "nochg":
                    return log_success_if_nochg
                else:
                    return False
                    
            except Exception as e:
                log(f"Unified provider failed, falling back to legacy: {str(e)}", "DEBUG", "PROVIDER")
                # Continue to legacy implementation below
        
        # Legacy implementation (kept for backward compatibility)
        # Cloudflare
        if protocol == "cloudflare":
            result = update_cloudflare(provider, ip, ip6)
            if result == "updated":
                msg = f"Provider '{provider_name}' updated successfully. New IP: {ip}"
                if old_ip is not None:
                    msg += f" (previous: {old_ip})"
                log(msg, "INFO", section="CLOUDFLARE")
                send_notifications(
                    config.get("notify"),
                    "UPDATE",
                    msg,
                    subject=f"DynDNS Update: {provider_name}",
                    service_name=provider_name
                )
            elif result == "nochg":
                if log_success_if_nochg:
                    log(f"Provider '{provider_name}' was already up to date, no update performed.", "TRACE", section="CLOUDFLARE")
            else:
                error_msg = f"Provider '{provider_name}' update failed. See previous log for details."
                log(error_msg, "ERROR", section="CLOUDFLARE")
                send_notifications(
                    config.get("notify"),
                    "ERROR",
                    f"Update failed for provider '{provider_name}' (Cloudflare). See logs for details.",
                    subject=f"DynDNS Error: {provider_name}",
                    service_name=provider_name
                )
            return result == "updated" or (log_success_if_nochg and result == "nochg")
        # ipv64
        if protocol == "ipv64":
            result = update_ipv64(provider, ip, ip6)
            if result == "updated":
                msg = f"Provider '{provider_name}' updated successfully. New IP: {ip}"
                if old_ip is not None:
                    msg += f" (previous: {old_ip})"
                log(msg, "INFO", section="IPV64")
                send_notifications(
                    config.get("notify"),
                    "UPDATE",
                    msg,
                    subject=f"DynDNS Update: {provider_name}",
                    service_name=provider_name
                )
            elif result == "nochg":
                if log_success_if_nochg:
                    log(f"Provider '{provider_name}' was already up to date, no update performed.", "TRACE", section="IPV64")
            else:
                error_msg = f"Provider '{provider_name}' update failed. See previous log for details."
                log(error_msg, "ERROR", section="IPV64")
                send_notifications(
                    config.get("notify"),
                    "ERROR",
                    f"Update failed for provider '{provider_name}' (ipv64). See logs for details.",
                    subject=f"DynDNS Error: {provider_name}",
                    service_name=provider_name
                )
            return result == "updated" or (log_success_if_nochg and result == "nochg")
        # dyndns2
        if protocol == "dyndns2":
            result = update_dyndns2(provider, ip, ip6)
            if result == "updated":
                msg = f"Provider '{provider_name}' updated successfully. New IP: {ip}"
                if old_ip is not None:
                    msg += f" (previous: {old_ip})"
                log(msg, "INFO", section="DYNDNS2")
                send_notifications(
                    config.get("notify"),
                    "UPDATE",
                    msg,
                    subject=f"DynDNS Update: {provider_name}",
                    service_name=provider_name
                )
            elif result == "nochg":
                if log_success_if_nochg:
                    log(f"Provider '{provider_name}' was already up to date, no update performed.", "TRACE", section="DYNDNS2")
            else:
                error_msg = f"Provider '{provider_name}' update failed. See previous log for details."
                log(error_msg, "ERROR", section="DYNDNS2")
                send_notifications(
                    config.get("notify"),
                    "ERROR",
                    f"Update failed for provider '{provider_name}' (dyndns2). See logs for details.",
                    subject=f"DynDNS Error: {provider_name}",
                    service_name=provider_name
                )
            return result == "updated" or (log_success_if_nochg and result == "nochg")
    except Exception as e:
        provider_name = provider.get("name", "PROVIDER")
        error_msg = f"Update for provider '{provider_name}' failed: {e}"
        log(error_msg, "ERROR", section=provider_name.upper())
        
        # Check if notify is configured before using it
        notify_config = config.get("notify") if config else None
        if notify_config:
            send_notifications(
                notify_config,
                "ERROR",
                error_msg,
                subject=f"DynDNS Error: {provider_name}",
                service_name=provider_name
            )
            
        return

def get_interface_ipv4(interface_name):
    """
    Gets the IPv4 address from the specified network interface.
    """
    log(f"Attempting to get IPv4 from interface '{interface_name}'", "DEBUG", section="INTERFACE")
    try:
        # Try using socket library directly (works on Linux)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 0x8915 is SIOCGIFADDR in Linux
        ifreq = struct.pack('256s', interface_name[:15].encode('utf-8'))
        try:
            if fcntl:  # Only use fcntl on Linux/Unix systems
                info = fcntl.ioctl(sock.fileno(), 0x8915, ifreq)
                ip = socket.inet_ntoa(info[20:24])
                if validate_ipv4(ip):
                    log(f"Found IPv4 address {ip} on interface '{interface_name}'", "INFO", section="INTERFACE")
                    return ip
        except OSError:
            pass  # Fall through to alternative method
        
        # Alternative method: Check all interfaces
        for addr_info in socket.getaddrinfo(socket.gethostname(), None):
            if addr_info[0] == socket.AF_INET:  # IPv4
                ip = addr_info[4][0]
                if validate_ipv4(ip) and ip != '127.0.0.1':
                    # Try to verify this belongs to our interface
                    try:
                        with open(f"/sys/class/net/{interface_name}/address") as f:
                            # Interface exists
                            log(f"Found IPv4 address {ip} that might be on interface '{interface_name}'", "INFO", section="INTERFACE")
                            return ip
                    except:
                        pass

        log(f"No IPv4 address found for interface '{interface_name}'", "WARNING", section="INTERFACE")
        return None
    except Exception as e:
        log(f"Error getting IPv4 address from interface '{interface_name}': {e}", "ERROR", section="INTERFACE")
        return None

def get_interface_ipv6(interface_name):
    """
    Gets the IPv6 address from the specified network interface using Python standard library.
    No external commands required.
    """
    try:
        # Check if interface exists
        try:
            with open(f"/sys/class/net/{interface_name}/address"):
                pass  # Interface exists
        except FileNotFoundError:
            log(f"Interface '{interface_name}' not found", "ERROR", section="INTERFACE")
            return None
            
        # Get all IPv6 addresses
        for addr_info in socket.getaddrinfo(socket.gethostname(), None):
            if addr_info[0] == socket.AF_INET6:  # IPv6
                ip = addr_info[4][0]
                # Remove scope ID if present
                if '%' in ip:
                    ip = ip.split('%')[0]
                
                # Skip link-local addresses
                if ip.startswith('fe80:'):
                    continue
                    
                if validate_ipv6(ip):
                    log(f"Found IPv6 address {ip} that might be on interface '{interface_name}'", "INFO", section="INTERFACE")
                    return ip
        
        log(f"No valid public IPv6 address found on interface '{interface_name}'", "WARNING", section="INTERFACE")
        return None
    except Exception as e:
        log(f"Error getting IPv6 address from interface '{interface_name}': {e}", "ERROR", section="INTERFACE")
        return None

def validate_ipv4(ip):
    """
    Validates if the given string is a valid IPv4 address.
    """
    try:
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        for part in parts:
            if not part.isdigit() or int(part) < 0 or int(part) > 255:
                return False
        return True
    except:
        return False

def validate_ipv6(ip):
    """
    Validates if the given string is a valid IPv6 address.
    More strict checking to prevent IPv4 addresses being accepted.
    """
    try:
        # Quick check: IPv6 address must contain at least one colon
        if ':' not in ip:
            return False
            
        # If it contains a dot, it might be an IPv4-mapped IPv6 address
        if '.' in ip and not ip.startswith('::ffff:'):
            return False
            
        socket.inet_pton(socket.AF_INET6, ip)
        return True
    except:
        return False

class IPResolver:
    """Unified IP resolution for IPv4 and IPv6 - eliminiert massive Duplikation."""
    
    def __init__(self, config):
        self.config = config
    
    def get_ip_with_fallback(self, ip_version='ipv4'):
        """
        Vereinheitlichte IP-Ermittlung für IPv4 und IPv6 mit Fallback-Strategien.
        
        Ersetzt:
        - get_public_ip_with_fallback()
        - get_public_ipv6_with_fallback()  
        - get_interface_ip_fallback()
        - get_interface_ipv6_fallback()
        
        Args:
            ip_version: 'ipv4' oder 'ipv6'
        
        Returns:
            IP-Adresse als String oder None bei Fehlschlag
        """
        services = self._get_services(ip_version)
        validator = validate_ipv4 if ip_version == 'ipv4' else validate_ipv6
        fetcher = get_public_ip if ip_version == 'ipv4' else get_public_ipv6
        
        log(f"Versuche {ip_version.upper()}-Ermittlung über {len(services)} Services...", "INFO", "NETWORK")
        
        # Try external services
        for i, service in enumerate(services, 1):
            try:
                log(f"{ip_version.upper()} Versuch {i}/{len(services)}: {service}", "DEBUG", "NETWORK")
                
                ip = fetcher(service)
                
                if ip and validator(ip):
                    log(f"{ip_version.upper()} erfolgreich ermittelt von {service}: {ip}", "INFO", "NETWORK")
                    return ip
                else:
                    log(f"⚠️ Ungültige {ip_version.upper()} von {service}: {ip}", "WARNING", "NETWORK")
                    
            except Exception as e:
                log(f"❌ {ip_version.upper()} Service {service} fehlgeschlagen: {str(e)}", "WARNING", "NETWORK")
                continue
        
        # Fallback to interface if enabled
        if self.config.get('enable_interface_fallback', True):
            interface_ip = self._get_interface_ip(ip_version)
            if interface_ip:
                log(f"{ip_version.upper()} erfolgreich von Interface ermittelt: {interface_ip}", "INFO", "NETWORK")
                return interface_ip
        
        # All methods failed
        log(f"❌ Alle {ip_version.upper()}-Services fehlgeschlagen", "ERROR", "NETWORK")
        return None
    
    def _get_services(self, ip_version):
        """Get service list for IP version - eliminiert Service-Listen-Duplikation."""
        if ip_version == 'ipv4':
            services = self.config.get('ip_services', [])
            if not services:
                primary_service = self.config.get('ip_service', 'https://api.ipify.org')
                fallback_services = [
                    "https://ifconfig.me/ip",
                    "https://icanhazip.com",
                    "https://checkip.amazonaws.com",
                    "https://ipecho.net/plain",
                    "https://myexternalip.com/raw"
                ]
                services = [primary_service] + fallback_services
        else:  # ipv6
            services = self.config.get('ip6_services', [])
            if not services:
                primary_service = self.config.get('ip6_service', 'https://api64.ipify.org')
                fallback_services = [
                    "https://ifconfig.me/ip",
                    "https://icanhazip.com",
                    "https://v6.ident.me",
                    "https://ipv6.icanhazip.com"
                ]
                services = [primary_service] + fallback_services
        
        # Add fallback services if not already included
        unique_services = []
        for service in services:
            if service not in unique_services:
                unique_services.append(service)
        
        return unique_services
    
    def _get_interface_ip(self, ip_version):
        """Get IP from network interface - eliminiert Interface-Fallback-Duplikation."""
        interface_key = 'interface' if ip_version == 'ipv4' else 'interface6'
        interface = self.config.get(interface_key)
        
        if not interface:
            log(f"Kein {interface_key} konfiguriert", "DEBUG", "NETWORK")
            return None
        
        log(f"Verwende Interface-Fallback für {ip_version.upper()}: {interface}", "INFO", "NETWORK")
        
        try:
            if ip_version == 'ipv4':
                return get_interface_ipv4(interface)
            else:
                return get_interface_ipv6(interface)
        except Exception as e:
            log(f"Interface-Fallback für {ip_version.upper()} fehlgeschlagen: {e}", "WARNING", "NETWORK")
            return None

# Backward compatibility functions - verwenden neue IPResolver
def get_public_ip_with_fallback(config):
    """Backward compatibility wrapper - verwendet neue IPResolver Klasse."""
    resolver = IPResolver(config)
    return resolver.get_ip_with_fallback('ipv4')

def get_public_ipv6_with_fallback(config):
    """Backward compatibility wrapper - verwendet neue IPResolver Klasse."""
    resolver = IPResolver(config)
    return resolver.get_ip_with_fallback('ipv6')

def get_interface_ip_fallback(config):
    """Backward compatibility wrapper - verwendet neue IPResolver Klasse."""
    resolver = IPResolver(config)
    return resolver._get_interface_ip('ipv4')

def get_interface_ipv6_fallback(config):
    """Backward compatibility wrapper - verwendet neue IPResolver Klasse."""
    resolver = IPResolver(config)
    return resolver._get_interface_ip('ipv6')

def get_current_ip_resilient(config):
    """Backward compatibility wrapper - verwendet neue IPResolver Klasse."""
    resolver = IPResolver(config)
    return resolver.get_ip_with_fallback('ipv4')

def get_current_ipv6_resilient(config):
    """Backward compatibility wrapper - verwendet neue IPResolver Klasse."""
    resolver = IPResolver(config)
    return resolver.get_ip_with_fallback('ipv6')

def handle_no_ip_available(consecutive_failures, config):
    """
    Behandelt den Fall, dass keine IP ermittelt werden konnte
    
    Args:
        consecutive_failures: Anzahl aufeinanderfolgender Fehler
        config: Konfigurationsdictionary
        
    Returns:
        Tuple: (neue consecutive_failures, Wartezeit in Sekunden)
    """
    consecutive_failures += 1
    
    # Basis-Wartezeit (Standard: 60 Sekunden)
    base_wait_time = config.get('network_retry_interval', 60)
    
    # Exponential Backoff nach mehreren Fehlern
    max_failures_before_backoff = config.get('max_failures_before_backoff', 5)
    
    if consecutive_failures <= max_failures_before_backoff:
        wait_time = base_wait_time
        log(f"⚠️ Keine IP verfügbar (Fehler #{consecutive_failures}). Warte {wait_time}s...", 
            "WARNING", "NETWORK")
    else:
        # Exponential Backoff: 60s, 120s, 240s, max 600s (10 Min)
        backoff_multiplier = config.get('backoff_multiplier', 2.0)
        max_wait_time = config.get('max_wait_time', 600)
        
        backoff_factor = min(consecutive_failures - max_failures_before_backoff, 4)
        wait_time = min(base_wait_time * (backoff_multiplier ** backoff_factor), max_wait_time)
        
        log(f"⚠️ Anhaltende Netzwerkprobleme (Fehler #{consecutive_failures}). "
            f"Exponential Backoff: Warte {wait_time}s...", "WARNING", "NETWORK")
    
    return consecutive_failures, wait_time

def main():
    global config, log_level, console_level
    
    # Initialize state configuration
    state.config = None
    
    config_path = 'config/config.yaml'
    if not os.path.exists(config_path):
        setup_logging("INFO")
        log("config/config.yaml not found! Please provide your own configuration or copy config.example.yaml.\n"
            "See instructions in the repository: https://github.com/alex-1987/dyndns-docker-client\n"
            "Example for Docker Compose:\n"
            "  volumes:\n"
            "    - ./config:/app/config\n"
            "and place your config.yaml in the ./config directory on the host.",
            "CRITICAL"
        )
        sys.exit(1)
    with open(config_path, 'r') as f:
        try:
            config = yaml.safe_load(f)
            state.config = config  # Update state
        except Exception as e:
            setup_logging("INFO")
            log(f"Error loading config.yaml: {e}", "ERROR")
            sys.exit(1)
    loglevel = config.get("loglevel", "INFO")
    consolelevel = config.get("consolelevel", loglevel)
    
    # Initialize logging FIRST before setting state variables
    setup_logging(loglevel, config)
    
    # Then update both state and global variables for backward compatibility
    log_level = loglevel
    console_level = consolelevel
    state.log_level = loglevel
    state.console_level = consolelevel
    
    # Test debug logging immediately after setup
    log(f"Logging system initialized: file_level='{loglevel}', console_level='{consolelevel}'", "DEBUG", "LOGGING")
    log("Testing DEBUG level logging - this message should appear if consolelevel is DEBUG", "DEBUG", "LOGGING")
    
    last_config_mtime = os.path.getmtime(config_path)
    if not config or not isinstance(config, dict):
        log(
            "config.yaml is empty or invalid! Please check the file and refer to config.example.yaml.\n"
            "See instructions in the repository: https://github.com/alex-1987/dyndns-docker-client",
            "CRITICAL"
        )
        sys.exit(1)
    if "providers" not in config or not isinstance(config["providers"], list) or not config["providers"]:
        log(
            "config.yaml does not contain any providers! Please add at least one provider under 'providers:'.\n"
            "See instructions and examples in the repository: https://github.com/alex-1987/dyndns-docker-client",
            "CRITICAL"
        )
        sys.exit(1)
    if not validate_config(config):
        log("Configuration invalid. Program will exit.", "CRITICAL")
        sys.exit(1)
    timer = config.get('timer', 300)
    providers = config['providers']

    # Get IP configuration method - support both singular and plural forms
    ip_service = config.get('ip_service', None)
    ip_services = config.get('ip_services', [])
    ip_interface = config.get('interface', None)
    ip6_service = config.get('ip6_service', None)
    ip6_services = config.get('ip6_services', [])
    ip6_interface = config.get('interface6', None)
    
    # If ip_services is provided but ip_service is not, use the first service from the list
    if not ip_service and ip_services:
        ip_service = ip_services[0]
    
    # If ip6_services is provided but ip6_service is not, use the first service from the list
    if not ip6_service and ip6_services:
        ip6_service = ip6_services[0]
    
    # Log the configuration
    if ip_service:
        if ip_services and len(ip_services) > 1:
            log(f"Using primary service to determine IPv4: {ip_service} (with {len(ip_services)-1} fallback services)", section="MAIN")
        else:
            log(f"Using service to determine IPv4: {ip_service}", section="MAIN")
    elif ip_interface:
        log(f"Using interface to determine IPv4: {ip_interface}", section="MAIN") 
    else:
        log("No method configured to determine IPv4", "WARNING", section="MAIN")
    if ip6_service:
        if ip6_services and len(ip6_services) > 1:
            log(f"Using primary service to determine IPv6: {ip6_service} (with {len(ip6_services)-1} fallback services)", section="MAIN")
        else:
            log(f"Using service to determine IPv6: {ip6_service}", section="MAIN")
    elif ip6_interface:
        log(f"Using interface to determine IPv6: {ip6_interface}", section="MAIN")
    
    # Get IPv4 address
    test_ip = None
    if ip_service:
        test_ip = get_public_ip(ip_service)
    elif ip_interface:
        test_ip = get_interface_ipv4(ip_interface)
        
    # Get IPv6 address
    test_ip6 = None
    if ip6_service:
        test_ip6 = get_public_ipv6(ip6_service)
    elif ip6_interface:
        test_ip6 = get_interface_ipv6(ip6_interface)
    
    # Validate IPs and send notifications for invalid IPs
    if test_ip is not None and not validate_ipv4(test_ip):
        error_msg = f"Invalid IPv4 address detected: {test_ip}"
        log(error_msg, "ERROR", section="MAIN")
        send_notifications(config.get("notify"), "ERROR", error_msg, "Invalid IPv4 Address")
        test_ip = None
        
    if test_ip6 is not None and not validate_ipv6(test_ip6):
        error_msg = f"Invalid IPv6 address detected: {test_ip6}"
        log(error_msg, "ERROR", section="MAIN")
        send_notifications(config.get("notify"), "ERROR", error_msg, "Invalid IPv6 Address")
        test_ip6 = None
    
    if not test_ip and not test_ip6:
        # Resilientes Verhalten: Statt Programm zu beenden, Fehler loggen und weiter versuchen
        log("⚠️ Keine gültige IP-Adresse konnte ermittelt werden. Aktiviere resilientes Netzwerkverhalten...", "WARNING", "MAIN")
        # Setze flag für resiliente Hauptschleife
        resilient_mode = True
        state.resilient_mode = True
        test_ip = None
        test_ip6 = None
    else:
        resilient_mode = False
        state.resilient_mode = False
    
    # --- PATCH: skip_update_on_startup ---
    skip_on_startup = config.get("skip_update_on_startup", False)
    last_ip = load_last_ip("v4")
    last_ip6 = load_last_ip("v6")
    ip_changed = (test_ip != last_ip) if test_ip else False
    ip6_changed = (test_ip6 != last_ip6) if test_ip6 else False

    if skip_on_startup and not ip_changed and not ip6_changed:
        log("IP has not changed since last run. No provider updates needed on startup.", "TRACE", section="MAIN")
        # IPs trotzdem speichern, falls sie vorher noch nicht gespeichert waren
        save_last_ip("v4", test_ip)
        save_last_ip("v6", test_ip6)
        last_ip = test_ip
        last_ip6 = test_ip6
        # Update state
        state.last_ipv4 = test_ip
        state.last_ipv6 = test_ip6
    else:
        log("Starting initial update run for all providers...", section="MAIN")
        failed_providers = []
        state.failed_providers = []
        for provider in providers:
            result = update_provider(provider, test_ip, test_ip6)
            section = provider.get('name', 'PROVIDER').upper()
            if not (result or result == "nochg"):
                log(f"Provider '{provider.get('name')}' could not be updated initially.", "WARNING", section=section)
                failed_providers.append(provider)
                state.add_failed_provider(provider.get('name', 'unknown'))
        save_last_ip("v4", test_ip)
        save_last_ip("v6", test_ip6)
        last_ip = test_ip
        last_ip6 = test_ip6
        # Update state
        state.last_ipv4 = test_ip
        state.last_ipv6 = test_ip6
        last_ip6 = test_ip6
    # --- END PATCH ---

    elapsed = 0
    check_interval = 2  # Seconds, how often to check for config changes

    log(f"Next run in {timer} seconds...", "DEBUG", section="MAIN")

    while True:
        time.sleep(check_interval)
        elapsed += check_interval

        # Check if config has changed
        current_mtime = os.path.getmtime(config_path)
        if current_mtime != last_config_mtime:
            log("Change in config.yaml detected. Reloading configuration and starting a new run.", section="MAIN")
            with open(config_path, 'r') as f:
                try:
                    config = yaml.safe_load(f)
                    state.config = config  # Update state
                except Exception as e:
                    log(f"Error loading config.yaml after change: {e}\nPlease check the file and refer to config.example.yaml.", "ERROR")
                    continue
            if not validate_config(config):
                log("Configuration invalid after change. Waiting for next change...", "ERROR")
                continue
            
            # Reload logging configuration
            new_loglevel = config.get("loglevel", "INFO")
            new_consolelevel = config.get("consolelevel", new_loglevel)
            if new_loglevel != log_level or new_consolelevel != console_level:
                log(f"Updating log levels: loglevel={new_loglevel}, consolelevel={new_consolelevel}", "INFO", section="MAIN")
                # Update both state and global variables
                log_level = new_loglevel
                console_level = new_consolelevel
                state.log_level = new_loglevel
                state.console_level = new_consolelevel
                setup_logging(new_loglevel, config)
            
            timer = config.get('timer', 300)
            ip_service = config.get('ip_service', None)
            ip_interface = config.get('interface', None)
            ip6_service = config.get('ip6_service', None)
            ip6_interface = config.get('interface6', None)
            providers = config['providers']
            last_config_mtime = current_mtime
            
            # Get current IPs using updated configuration with resilient handling
            current_ip = None
            if ip_service:
                try:
                    current_ip = get_public_ip(ip_service)
                except Exception as e:
                    log(f"❌ IP-Service Fehler nach Config-Reload: {e}", "ERROR", "NETWORK")
                    current_ip = get_current_ip_resilient(config)
            elif ip_interface:
                try:
                    current_ip = get_interface_ipv4(ip_interface)
                except Exception as e:
                    log(f"❌ Interface Fehler nach Config-Reload: {e}", "ERROR", "NETWORK")
                    current_ip = get_current_ip_resilient(config)
            else:
                # Kein Service/Interface konfiguriert - verwende resiliente Methode
                current_ip = get_current_ip_resilient(config)
                
            current_ip6 = None
            if config.get('ip6_service') or config.get('ip6_services'):
                try:
                    current_ip6 = get_current_ipv6_resilient(config)
                except Exception as e:
                    log(f"IPv6 Resilient Service Fehler nach Config-Reload: {e}", "WARNING", "NETWORK")
            elif ip6_interface:
                try:
                    current_ip6 = get_interface_ipv6(ip6_interface)
                except Exception as e:
                    log(f"IPv6 Interface Fehler nach Config-Reload: {e}", "WARNING", "NETWORK")
            if current_ip:
                log(f"Current public IP: {current_ip}", "TRACE", section="MAIN")
            if current_ip6:
                log(f"Current public IPv6: {current_ip6}", "TRACE", section="MAIN")
            failed_providers = []
            state.failed_providers = []
            for provider in providers:
                result = update_provider(provider, current_ip, current_ip6)
                section = provider.get('name', 'PROVIDER').upper()
                if not result:  # update_provider returns True for success (updated/nochg), False for failure
                    log(f"Provider '{provider.get('name')}' could not be updated after config change.", "WARNING", section=section)
                    failed_providers.append(provider)
                    state.add_failed_provider(provider.get('name', 'unknown'))
            last_ip = current_ip
            last_ip6 = current_ip6
            # Update state
            state.last_ipv4 = current_ip
            state.last_ipv6 = current_ip6
            elapsed = 0
            log(f"Next run in {timer} seconds...", "DEBUG", section="MAIN")
            continue

        # Timer-based update with resilient network handling
        if elapsed >= timer:
            if resilient_mode or state.resilient_mode:
                # Verwende resiliente IP-Ermittlung
                current_ip = get_current_ip_resilient(config)
                
                # IPv6 resilient 
                current_ip6 = None
                if config.get('ip6_service') or config.get('ip6_services') or config.get('interface6'):
                    current_ip6 = get_current_ipv6_resilient(config)
                        
                if not current_ip and not current_ip6:
                    # Keine IP verfügbar - resiliente Behandlung
                    if not hasattr(main, 'consecutive_failures'):
                        main.consecutive_failures = 0
                    
                    main.consecutive_failures, wait_time = handle_no_ip_available(main.consecutive_failures, config)
                    
                    log("🔄 Programm läuft weiter trotz Netzwerkproblemen...", "INFO", "MAIN")
                    
                    # Warte entsprechend der Backoff-Strategie
                    elapsed = 0
                    # Überschreibe timer temporär für Backoff
                    original_timer = timer
                    timer = wait_time
                    log(f"⏳ Nächster IP-Versuch in {timer} Sekunden...", "DEBUG", "MAIN")
                    continue
                else:
                    # IP erfolgreich ermittelt - Reset failure counter
                    if hasattr(main, 'consecutive_failures') and main.consecutive_failures > 0:
                        log(f"✅ Netzwerk wiederhergestellt nach {main.consecutive_failures} Fehlern", "INFO", "NETWORK")
                        main.consecutive_failures = 0
                    
                    # Resilient mode deaktivieren wenn wir wieder IPs haben
                    resilient_mode = False
                    state.resilient_mode = False
                    
                    # Timer auf ursprünglichen Wert zurücksetzen
                    timer = config.get('timer', 300)
            else:
                # Normale IP-Ermittlung
                current_ip = None
                if ip_service:
                    try:
                        current_ip = get_public_ip(ip_service)
                    except Exception as e:
                        log(f"❌ IP-Service Fehler: {e}", "ERROR", "NETWORK")
                        # Versuche resiliente IP-Ermittlung, aber aktiviere resilient_mode noch nicht
                        current_ip = get_current_ip_resilient(config)
                elif ip_interface:
                    try:
                        current_ip = get_interface_ipv4(ip_interface)
                    except Exception as e:
                        log(f"❌ Interface Fehler: {e}", "ERROR", "NETWORK")
                        current_ip = None
                        
                current_ip6 = None
                if config.get('ip6_service') or config.get('ip6_services'):
                    try:
                        current_ip6 = get_current_ipv6_resilient(config)
                    except Exception as e:
                        log(f"IPv6 Resilient Service Fehler: {e}", "WARNING", "NETWORK")
                elif ip6_interface:
                    try:
                        current_ip6 = get_interface_ipv6(ip6_interface)
                    except Exception as e:
                        log(f"IPv6 Interface Fehler: {e}", "WARNING", "NETWORK")
                
                # Fallback zu resilient mode wenn keine IP ermittelt werden konnte
                if not current_ip and not current_ip6:
                    log("🔄 Aktiviere resilientes Netzwerkverhalten aufgrund von Fehlern...", "WARNING", "MAIN")
                    resilient_mode = True
                    state.resilient_mode = True
                    continue
                
            # Check for IP change or failed providers
            ip_changed = (current_ip != last_ip) if current_ip is not None else False
            ip6_changed = (current_ip6 != last_ip6) if current_ip6 is not None else False
            
            # Log current IPs: INFO if changed, TRACE if unchanged
            if current_ip:
                if ip_changed:
                    log(f"Current public IP: {current_ip}", "INFO", section="MAIN")
                else:
                    log(f"Current public IP: {current_ip}", "TRACE", section="MAIN")
            if current_ip6:
                if ip6_changed:
                    log(f"Current public IPv6: {current_ip6}", "INFO", section="MAIN")
                else:
                    log(f"Current public IPv6: {current_ip6}", "TRACE", section="MAIN")
                    
            # Perform updates if needed
            if ip_changed or ip6_changed or failed_providers or state.failed_providers:
                if ip_changed:
                    log(f"New IP detected: {current_ip} (previous: {last_ip}) – update will be performed.", section="MAIN")
                if ip6_changed:
                    log(f"New IPv6 detected: {current_ip6} (previous: {last_ip6}) – update will be performed.", section="MAIN")
                    
                # Update all providers (retry failed providers always)
                retry_providers = failed_providers.copy()
                failed_providers = []
                state.failed_providers = []
                
                for provider in providers:
                    # Retry if provider was in failed_providers or IP changed
                    if provider in retry_providers or ip_changed or ip6_changed:
                        try:
                            result = update_provider(provider, current_ip, current_ip6)
                            section = provider.get('name', 'PROVIDER').upper()
                            if not result:  # update_provider returns True for success (updated/nochg), False for failure
                                failed_providers.append(provider)
                                state.add_failed_provider(provider.get('name', 'unknown'))
                        except Exception as e:
                            log(f"Provider update failed: {provider.get('name')} - {e}", "ERROR", "PROVIDER")
                            failed_providers.append(provider)
                            state.add_failed_provider(provider.get('name', 'unknown'))
                            
                # Save last known IPs
                if current_ip:
                    save_last_ip("v4", current_ip)
                if current_ip6:
                    save_last_ip("v6", current_ip6)
                    
                last_ip = current_ip
                last_ip6 = current_ip6
                # Update state
                state.last_ipv4 = current_ip
                state.last_ipv6 = current_ip6
                elapsed = 0
                log(f"Next run in {timer} seconds...", "DEBUG", section="MAIN")
            else:
                if current_ip:
                    log(f"IP unchanged ({current_ip}), no update needed.", "TRACE", section="MAIN")
                if current_ip6:
                    log(f"IPv6 unchanged ({current_ip6}), no update needed.", "TRACE", section="MAIN")
                elapsed = 0
                log(f"Next run in {timer} seconds...", "DEBUG", section="MAIN")

if __name__ == "__main__":
    main()