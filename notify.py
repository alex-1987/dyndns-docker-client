import requests
import logging
import smtplib
import time
import os
from email.mime.text import MIMEText

def human_error_message(e, context=""):
    """
    Returns a human-readable error message for common network errors.
    """
    err_str = str(e)
    if "[Errno -2]" in err_str:
        return f"{context} failed: Hostname not found (DNS issue or typo in server name)."
    elif "[Errno 111]" in err_str:
        return f"{context} failed: Connection refused (server not reachable or wrong port)."
    elif "[Errno 110]" in err_str:
        return f"{context} failed: Timeout while connecting."
    elif "Name or service not known" in err_str:
        return f"{context} failed: Hostname not found (DNS issue or typo in server name)."
    else:
        return f"{context} failed: {e}"

def _cooldown_file(service):
    """
    Returns the path to the cooldown file for the given notification service.
    Uses OS-appropriate temporary directory for cross-platform compatibility.
    """
    import tempfile
    return os.path.join(tempfile.gettempdir(), f"notify_cooldown_{service}.txt")

def _can_send_notification(service, cooldown_minutes):
    """
    Checks if a notification can be sent for the given service,
    based on the cooldown period.
    """
    try:
        from update_dyndns import log
        debug_log = lambda msg: log(msg, "DEBUG", "NOTIFY")
    except ImportError:
        debug_log = lambda msg: None
    
    if not cooldown_minutes or cooldown_minutes <= 0:
        debug_log(f"No cooldown configured for {service} - notification allowed")
        return True
        
    path = _cooldown_file(service)
    if not os.path.exists(path):
        debug_log(f"No cooldown file found for {service} - first notification allowed")
        return True
        
    try:
        with open(path, "r") as f:
            last = float(f.read())
        time_since_last = time.time() - last
        remaining_cooldown = (cooldown_minutes * 60) - time_since_last
        
        if remaining_cooldown <= 0:
            debug_log(f"Cooldown expired for {service} - notification allowed")
            return True
        else:
            debug_log(f"Cooldown active for {service} - {remaining_cooldown:.0f}s remaining")
            return False
            
    except (ValueError, IOError) as e:
        debug_log(f"Error reading cooldown file for {service}: {e} - allowing notification")
        return True

def _update_last_notification_time(service):
    """
    Updates the cooldown file with the current time for the given service.
    """
    try:
        from update_dyndns import log
        log(f"Updating cooldown timer for {service}", "DEBUG", "NOTIFY")
    except ImportError:
        pass
        
    with open(_cooldown_file(service), "w") as f:
        f.write(str(time.time()))

def notify_ntfy(url, message, service_name=None):
    """
    Sends a notification via ntfy.
    """
    try:
        # Import log function for debug info
        try:
            from update_dyndns import log
            log(f"Sending ntfy notification to {url[:50]}... (service: {service_name})", "DEBUG", "NOTIFY")
        except ImportError:
            pass
            
        msg = f"[{service_name}] {message}" if service_name else message
        response = requests.post(url, data=msg.encode("utf-8"), timeout=5)
        
        try:
            from update_dyndns import log
            log(f"ntfy notification sent successfully (status: {response.status_code})", "DEBUG", "NOTIFY")
        except ImportError:
            pass
            
    except Exception as e:
        logging.getLogger("NOTIFY").warning(human_error_message(e, "ntfy-Notification"))
        try:
            from update_dyndns import log
            log(f"ntfy notification failed: {str(e)}", "DEBUG", "NOTIFY")
        except ImportError:
            pass

def notify_discord(webhook_url, message, service_name=None):
    """
    Sends a notification via Discord webhook.
    """
    try:
        # Import log function for debug info
        try:
            from update_dyndns import log
            log(f"Sending Discord notification to webhook (service: {service_name})", "DEBUG", "NOTIFY")
        except ImportError:
            pass
            
        msg = f"[{service_name}] {message}" if service_name else message
        data = {"content": msg}
        response = requests.post(webhook_url, json=data, timeout=5)
        
        try:
            from update_dyndns import log
            log(f"Discord notification sent successfully (status: {response.status_code})", "DEBUG", "NOTIFY")
        except ImportError:
            pass
            
    except Exception as e:
        logging.getLogger("NOTIFY").warning(human_error_message(e, "Discord-Notification"))
        try:
            from update_dyndns import log
            log(f"Discord notification failed: {str(e)}", "DEBUG", "NOTIFY")
        except ImportError:
            pass

def notify_slack(webhook_url, message, service_name=None):
    """
    Sends a notification via Slack webhook.
    """
    try:
        # Import log function for debug info
        try:
            from update_dyndns import log
            log(f"Sending Slack notification to webhook (service: {service_name})", "DEBUG", "NOTIFY")
        except ImportError:
            pass
            
        msg = f"[{service_name}] {message}" if service_name else message
        data = {"text": msg}
        response = requests.post(webhook_url, json=data, timeout=5)
        
        try:
            from update_dyndns import log
            log(f"Slack notification sent successfully (status: {response.status_code})", "DEBUG", "NOTIFY")
        except ImportError:
            pass
            
    except Exception as e:
        logging.getLogger("NOTIFY").warning(human_error_message(e, "Slack-Notification"))
        try:
            from update_dyndns import log
            log(f"Slack notification failed: {str(e)}", "DEBUG", "NOTIFY")
        except ImportError:
            pass

def notify_webhook(url, message, service_name=None):
    """
    Sends a notification via a generic webhook.
    """
    try:
        # Import log function for debug info
        try:
            from update_dyndns import log
            log(f"Sending webhook notification to {url[:50]}... (service: {service_name})", "DEBUG", "NOTIFY")
        except ImportError:
            pass
            
        msg = f"[{service_name}] {message}" if service_name else message
        data = {"message": msg}
        response = requests.post(url, json=data, timeout=5)
        
        try:
            from update_dyndns import log
            log(f"Webhook notification sent successfully (status: {response.status_code})", "DEBUG", "NOTIFY")
        except ImportError:
            pass
            
    except Exception as e:
        logging.getLogger("NOTIFY").warning(human_error_message(e, "Webhook-Notification"))
        try:
            from update_dyndns import log
            log(f"Webhook notification failed: {str(e)}", "DEBUG", "NOTIFY")
        except ImportError:
            pass

def notify_telegram(bot_token, chat_id, message, service_name=None):
    """
    Sends a notification via Telegram bot.
    """
    try:
        # Import log function for debug info
        try:
            from update_dyndns import log
            log(f"Sending Telegram notification to chat {chat_id} (service: {service_name})", "DEBUG", "NOTIFY")
        except ImportError:
            pass
            
        msg = f"[{service_name}] {message}" if service_name else message
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {"chat_id": chat_id, "text": msg}
        response = requests.post(url, data=data, timeout=5)
        
        try:
            from update_dyndns import log
            log(f"Telegram notification sent successfully (status: {response.status_code})", "DEBUG", "NOTIFY")
        except ImportError:
            pass
            
    except Exception as e:
        logging.getLogger("NOTIFY").warning(human_error_message(e, "Telegram-Notification"))
        try:
            from update_dyndns import log
            log(f"Telegram notification failed: {str(e)}", "DEBUG", "NOTIFY")
        except ImportError:
            pass

def notify_email(cfg, subject, message, service_name=None):
    """
    Sends an email notification using the provided SMTP configuration.
    """
    try:
        # Import log function for debug info
        try:
            from update_dyndns import log
            log(f"Sending email notification to {cfg.get('to')} via {cfg.get('smtp_server')} (service: {service_name})", "DEBUG", "NOTIFY")
        except ImportError:
            pass
            
        msg_text = f"[{service_name}] {message}" if service_name else message
        msg = MIMEText(msg_text)
        msg["Subject"] = subject
        msg["From"] = cfg["from"]
        msg["To"] = cfg["to"]
        port = cfg.get("smtp_port", 587)
        if "smtp_ssl" in cfg:
            use_ssl = cfg["smtp_ssl"]
        elif port == 465:
            use_ssl = True
        else:
            use_ssl = False

        if "smtp_starttls" in cfg:
            use_starttls = cfg["smtp_starttls"]
        elif port == 587:
            use_starttls = True
        else:
            use_starttls = False

        if use_ssl:
            with smtplib.SMTP_SSL(cfg["smtp_server"], port) as server:
                if cfg.get("smtp_user") and cfg.get("smtp_pass"):
                    server.login(cfg["smtp_user"], cfg["smtp_pass"])
                server.sendmail(cfg["from"], [cfg["to"]], msg.as_string())
        else:
            with smtplib.SMTP(cfg["smtp_server"], port) as server:
                if use_starttls:
                    server.starttls()
                if cfg.get("smtp_user") and cfg.get("smtp_pass"):
                    server.login(cfg["smtp_user"], cfg["smtp_pass"])
                server.sendmail(cfg["from"], [cfg["to"]], msg.as_string())
                
        try:
            from update_dyndns import log
            log(f"Email notification sent successfully to {cfg.get('to')}", "DEBUG", "NOTIFY")
        except ImportError:
            pass
            
    except Exception as e:
        logging.getLogger("NOTIFY").warning(human_error_message(e, "E-Mail-Notification"))
        try:
            from update_dyndns import log
            log(f"Email notification failed: {str(e)}", "DEBUG", "NOTIFY")
        except ImportError:
            pass

def reset_all_cooldowns():
    """
    Deletes all cooldown files for all notification services.
    Used to reset cooldowns on container start if configured.
    """
    for service in ["ntfy", "discord", "slack", "webhook", "telegram", "email"]:
        try:
            os.remove(_cooldown_file(service))
        except FileNotFoundError:
            pass

def send_notifications(config, level, message, subject=None, service_name=None):
    """
    Unified notification sending with service registry - eliminiert massive Code-Duplikation.
    Vollständig kompatibel mit update_dyndns.py.
    """
    # Import log function - kompatibel mit update_dyndns.py
    try:
        from update_dyndns import log
    except ImportError:
        # Fallback if running standalone
        import datetime
        def log(msg, lv="INFO", section="NOTIFY"):
            print(f"{datetime.datetime.now().isoformat()} [{lv}] {section} --> {msg}")
    
    # Debug: Overall notification call
    log(f"=== NOTIFICATION DEBUG START ===", "DEBUG", "NOTIFY")
    log(f"send_notifications called: level='{level}', message='{message[:50]}...', service_name='{service_name}'", "DEBUG", "NOTIFY")
    
    # Check if configuration exists
    if not config:
        log("No notification configuration found - notifications disabled", "DEBUG", "NOTIFY")
        log(f"=== NOTIFICATION DEBUG END (no config) ===", "DEBUG", "NOTIFY")
        return
        
    log(f"Notification config found with {len(config)} services configured", "DEBUG", "NOTIFY")
    
    # Cooldown reset on container start
    if config.get("reset_cooldown_on_start"):
        log("Resetting all cooldown timers on container start", "DEBUG", "NOTIFY")
        reset_all_cooldowns()
        # Only execute once per start
        config["reset_cooldown_on_start"] = False

    # Service registry - eliminates code duplication
    services = {
        'ntfy': lambda cfg: notify_ntfy(cfg['url'], message, service_name),
        'discord': lambda cfg: notify_discord(cfg['webhook_url'], message, service_name),
        'slack': lambda cfg: notify_slack(cfg['webhook_url'], message, service_name),
        'telegram': lambda cfg: notify_telegram(cfg['bot_token'], cfg['chat_id'], message, service_name),
        'webhook': lambda cfg: notify_webhook(cfg['url'], message, service_name),
        'email': lambda cfg: notify_email(cfg, subject or "DynDNS Client Notification", message, service_name)
    }
    
    # Process each service using unified logic
    for service_name, send_func in services.items():
        _process_service_notification(config, service_name, level, send_func, log)
    
    log(f"=== NOTIFICATION DEBUG END (processing completed for level '{level}') ===", "DEBUG", "NOTIFY")

def _process_service_notification(config, service_name, level, send_func, log_func):
    """
    Process notification for a single service - eliminiert 90% Code-Duplikation.
    Einheitliche Logik für alle 6 Services.
    """
    cfg = config.get(service_name)
    
    # Helper for logging notification actions - kompatibel mit bestehendem Code
    def log_notify(service, sent, reason=""):
        logger = logging.getLogger("NOTIFY")
        if sent:
            logger.info(f"Notification sent via {service}.")
            log_func(f"Notification sent via {service}", "INFO", "NOTIFY")
        else:
            logger.info(f"Notification via {service} suppressed ({reason}).")
            log_func(f"Notification via {service} suppressed: {reason}", "DEBUG", "NOTIFY")
    
    # Helper for debug logging - kompatibel mit bestehendem Code
    def debug_service_check(service_name, cfg, level, enabled_check, level_check, cooldown_check=None):
        log_func(f"Checking {service_name} service:", "DEBUG", "NOTIFY")
        log_func(f"  - Config found: {cfg is not None}", "DEBUG", "NOTIFY")
        log_func(f"  - Enabled: {enabled_check}", "DEBUG", "NOTIFY") 
        log_func(f"  - Level '{level}' in notify_on {cfg.get('notify_on', []) if cfg else []}: {level_check}", "DEBUG", "NOTIFY")
        if cooldown_check is not None:
            log_func(f"  - Cooldown check passed: {cooldown_check}", "DEBUG", "NOTIFY")

    # Unified service processing logic
    enabled = cfg and cfg.get("enabled", False)
    level_match = enabled and level in cfg.get("notify_on", [])
    debug_service_check(service_name, cfg, level, enabled, level_match)
    
    if enabled and level_match:
        cooldown = cfg.get("cooldown", 0)
        can_send = _can_send_notification(service_name, cooldown)
        debug_service_check(service_name, cfg, level, enabled, level_match, can_send)
        
        if can_send:
            try:
                send_func(cfg)
                _update_last_notification_time(service_name)
                log_notify(service_name, True)
            except Exception as e:
                log_func(f"Failed to send {service_name} notification: {e}", "ERROR", "NOTIFY")
                log_notify(service_name, False, f"send failed: {e}")
        else:
            log_notify(service_name, False, "cooldown active")
    else:
        if not cfg:
            log_notify(service_name, False, "service not configured")
        elif not enabled:
            log_notify(service_name, False, "service disabled")
        elif not level_match:
            log_notify(service_name, False, f"level '{level}' not in notify_on list")