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
    if not cooldown_minutes or cooldown_minutes <= 0:
        return True
    path = _cooldown_file(service)
    if not os.path.exists(path):
        return True
    with open(path, "r") as f:
        last = float(f.read())
    return (time.time() - last) > cooldown_minutes * 60

def _update_last_notification_time(service):
    """
    Updates the cooldown file with the current time for the given service.
    """
    with open(_cooldown_file(service), "w") as f:
        f.write(str(time.time()))

def notify_ntfy(url, message, service_name=None):
    """
    Sends a notification via ntfy.
    """
    try:
        msg = f"[{service_name}] {message}" if service_name else message
        requests.post(url, data=msg.encode("utf-8"), timeout=5)
    except Exception as e:
        logging.getLogger("NOTIFY").warning(human_error_message(e, "ntfy-Notification"))

def notify_discord(webhook_url, message, service_name=None):
    """
    Sends a notification via Discord webhook.
    """
    try:
        msg = f"[{service_name}] {message}" if service_name else message
        data = {"content": msg}
        requests.post(webhook_url, json=data, timeout=5)
    except Exception as e:
        logging.getLogger("NOTIFY").warning(human_error_message(e, "Discord-Notification"))

def notify_slack(webhook_url, message, service_name=None):
    """
    Sends a notification via Slack webhook.
    """
    try:
        msg = f"[{service_name}] {message}" if service_name else message
        data = {"text": msg}
        requests.post(webhook_url, json=data, timeout=5)
    except Exception as e:
        logging.getLogger("NOTIFY").warning(human_error_message(e, "Slack-Notification"))

def notify_webhook(url, message, service_name=None):
    """
    Sends a notification via a generic webhook.
    """
    try:
        msg = f"[{service_name}] {message}" if service_name else message
        data = {"message": msg}
        requests.post(url, json=data, timeout=5)
    except Exception as e:
        logging.getLogger("NOTIFY").warning(human_error_message(e, "Webhook-Notification"))

def notify_telegram(bot_token, chat_id, message, service_name=None):
    """
    Sends a notification via Telegram bot.
    """
    try:
        msg = f"[{service_name}] {message}" if service_name else message
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {"chat_id": chat_id, "text": msg}
        requests.post(url, data=data, timeout=5)
    except Exception as e:
        logging.getLogger("NOTIFY").warning(human_error_message(e, "Telegram-Notification"))

def notify_email(cfg, subject, message, service_name=None):
    """
    Sends an email notification using the provided SMTP configuration.
    """
    try:
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
    except Exception as e:
        logging.getLogger("NOTIFY").warning(human_error_message(e, "E-Mail-Notification"))

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
    Sends notifications to all enabled notification services that 
    accept the given notification level.
    """
    # Check if configuration exists
    if not config:
        # No notifications configured, simply return
        return
        
    reset_cooldown = config.get("reset_cooldown_on_start", False)
    
    # Cooldown reset on container start
    if config.get("reset_cooldown_on_start"):
        reset_all_cooldowns()
        # Only execute once per start, e.g. via a global flag
        config["reset_cooldown_on_start"] = False

    if not config:
        return

    # Helper for logging notification actions
    def log_notify(service, sent, reason=""):
        logger = logging.getLogger("NOTIFY")
        if sent:
            logger.info(f"Notification sent via {service}.")
        else:
            logger.info(f"Notification via {service} suppressed ({reason}).")

    # ntfy
    ntfy_cfg = config.get("ntfy")
    if ntfy_cfg and ntfy_cfg.get("enabled") and level in ntfy_cfg.get("notify_on", []):
        cooldown = ntfy_cfg.get("cooldown", 0)
        if _can_send_notification("ntfy", cooldown):
            notify_ntfy(ntfy_cfg["url"], message, service_name)
            _update_last_notification_time("ntfy")
            log_notify("ntfy", True)
        else:
            log_notify("ntfy", False, "cooldown active")

    # Discord
    discord_cfg = config.get("discord")
    print(f"DEBUG: Discord config found: {discord_cfg is not None}")
    if discord_cfg:
        print(f"DEBUG: Discord enabled: {discord_cfg.get('enabled')}")
        print(f"DEBUG: Level '{level}' in notify_on {discord_cfg.get('notify_on', [])}: {level in discord_cfg.get('notify_on', [])}")
    
    if discord_cfg and discord_cfg.get("enabled") and level in discord_cfg.get("notify_on", []):
        cooldown = discord_cfg.get("cooldown", 0)
        print(f"DEBUG: Discord cooldown check - can send: {_can_send_notification('discord', cooldown)}")
        if _can_send_notification("discord", cooldown):
            print(f"DEBUG: Sending Discord notification...")
            notify_discord(discord_cfg["webhook_url"], message, service_name)
            _update_last_notification_time("discord")
            log_notify("discord", True)
        else:
            log_notify("discord", False, "cooldown active")
    else:
        print(f"DEBUG: Discord notification skipped - config ok: {discord_cfg is not None}, enabled: {discord_cfg.get('enabled') if discord_cfg else 'N/A'}, level check: {level in discord_cfg.get('notify_on', []) if discord_cfg else 'N/A'}")

    # Slack
    slack_cfg = config.get("slack")
    if slack_cfg and slack_cfg.get("enabled") and level in slack_cfg.get("notify_on", []):
        cooldown = slack_cfg.get("cooldown", 0)
        if _can_send_notification("slack", cooldown):
            notify_slack(slack_cfg["webhook_url"], message, service_name)
            _update_last_notification_time("slack")
            log_notify("slack", True)
        else:
            log_notify("slack", False, "cooldown active")

    # Webhook
    webhook_cfg = config.get("webhook")
    if webhook_cfg and webhook_cfg.get("enabled") and level in webhook_cfg.get("notify_on", []):
        cooldown = webhook_cfg.get("cooldown", 0)
        if _can_send_notification("webhook", cooldown):
            notify_webhook(webhook_cfg["url"], message, service_name)
            _update_last_notification_time("webhook")
            log_notify("webhook", True)
        else:
            log_notify("webhook", False, "cooldown active")

    # Telegram
    telegram_cfg = config.get("telegram")
    if telegram_cfg and telegram_cfg.get("enabled") and level in telegram_cfg.get("notify_on", []):
        cooldown = telegram_cfg.get("cooldown", 0)
        if _can_send_notification("telegram", cooldown):
            notify_telegram(telegram_cfg["bot_token"], telegram_cfg["chat_id"], message, service_name)
            _update_last_notification_time("telegram")
            log_notify("telegram", True)
        else:
            log_notify("telegram", False, "cooldown active")

    # Email
    email_cfg = config.get("email")
    if email_cfg and email_cfg.get("enabled") and level in email_cfg.get("notify_on", []):
        cooldown = email_cfg.get("cooldown", 0)
        if _can_send_notification("email", cooldown):
            notify_email(email_cfg, subject or "DynDNS Client Notification", message, service_name)
            _update_last_notification_time("email")
            log_notify("email", True)
        else:
            log_notify("email", False, "cooldown active")