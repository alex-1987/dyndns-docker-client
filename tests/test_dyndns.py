import pytest
import requests
import socket
import os
import json
from unittest.mock import patch, MagicMock, mock_open

# Import your modules - adjust imports as needed
import update_dyndns
import notify

# Tests for IP-related functions
class TestIPFunctions:
    @patch('requests.get')
    def test_get_public_ip(self, mock_get):
        # Setup mock
        mock_response = MagicMock()
        mock_response.text = "192.168.1.1\n"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Call function and test
        result = update_dyndns.get_public_ip("https://example.com/ip")
        assert result == "192.168.1.1"
        mock_get.assert_called_once_with("https://example.com/ip", timeout=10)
    
    @patch('requests.get')
    def test_get_public_ip_error(self, mock_get):
        # Test error handling
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")
        
        # Call function and verify logs
        with patch('update_dyndns.log') as mock_log:
            result = update_dyndns.get_public_ip("https://example.com/ip")
            assert result is None
            mock_log.assert_called_once()
    
    def test_validate_ipv4(self):
        # Valid IPs
        assert update_dyndns.validate_ipv4("192.168.1.1") is True
        assert update_dyndns.validate_ipv4("8.8.8.8") is True
        
        # Invalid IPs
        assert update_dyndns.validate_ipv4("256.0.0.1") is False
        assert update_dyndns.validate_ipv4("192.168.1") is False
        assert update_dyndns.validate_ipv4("not-an-ip") is False
    
    def test_validate_ipv6(self):
        # Valid IPv6
        assert update_dyndns.validate_ipv6("2001:0db8:85a3:0000:0000:8a2e:0370:7334") is True
        assert update_dyndns.validate_ipv6("::1") is True
        
        # Invalid IPv6
        assert update_dyndns.validate_ipv6("192.168.1.1") is False
        assert update_dyndns.validate_ipv6("not-an-ip") is False

# Tests for update functions
class TestUpdateFunctions:
    @patch('requests.get')
    def test_update_dyndns2_success(self, mock_get):
        # Setup mock
        mock_response = MagicMock()
        mock_response.text = "good 192.168.1.1"
        mock_get.return_value = mock_response
        
        # Create provider config
        provider = {
            "name": "test_provider",
            "url": "https://example.com/update",
            "auth_method": "basic",
            "username": "user", 
            "password": "pass",
            "hostname": "test.example.com"
        }
        
        # Call function and test
        with patch('update_dyndns.log'):
            result = update_dyndns.update_dyndns2(provider, "192.168.1.1")
            assert result == "updated"
    
    @patch('requests.get')
    def test_update_dyndns2_nochg(self, mock_get):
        # Test nochg response
        mock_response = MagicMock()
        mock_response.text = "nochg 192.168.1.1"
        mock_get.return_value = mock_response
        
        provider = {
            "name": "test_provider",
            "url": "https://example.com/update",
            "auth_method": "basic",
            "username": "user",
            "password": "pass",
            "hostname": "test.example.com"
        }
        
        with patch('update_dyndns.log'):
            result = update_dyndns.update_dyndns2(provider, "192.168.1.1")
            assert result == "nochg"
    
    @patch('requests.get')
    def test_update_dyndns2_with_extra_params(self, mock_get):
        # Test extra_params
        mock_response = MagicMock()
        mock_response.text = "good 192.168.1.1"
        mock_get.return_value = mock_response
        
        provider = {
            "name": "ovh_provider",
            "url": "https://www.ovh.com/nic/update",
            "auth_method": "basic",
            "username": "user",
            "password": "pass",
            "hostname": "test.example.com",
            "extra_params": {"system": "dyndns"}
        }
        
        with patch('update_dyndns.log'):
            result = update_dyndns.update_dyndns2(provider, "192.168.1.1")
            assert result == "updated"
            
            # Verify extra_params were included
            args, kwargs = mock_get.call_args
            assert kwargs.get("params", {}).get("system") == "dyndns"

# Tests for notification functions
class TestNotifications:
    @patch('requests.post')
    def test_notify_discord(self, mock_post):
        # Test Discord notification
        webhook_url = "https://discord.com/api/webhooks/123/abc"
        message = "Test message"
        service_name = "TestService"
        
        with patch('notify.logging.getLogger'):
            notify.notify_discord(webhook_url, message, service_name)
            
            # Verify Discord webhook was called with right data
            args, kwargs = mock_post.call_args
            assert args[0] == webhook_url
            assert kwargs.get("json", {}).get("content") == "[TestService] Test message"
    
    @patch('smtplib.SMTP')
    def test_notify_email(self, mock_smtp):
        # Test email notification
        cfg = {
            "from": "sender@example.com",
            "to": "recipient@example.com",
            "smtp_server": "smtp.example.com",
            "smtp_port": 587,
            "smtp_user": "user",
            "smtp_pass": "pass"
        }
        subject = "Test Subject"
        message = "Test message"
        
        # Setup mock SMTP instance
        mock_smtp_instance = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_smtp_instance
        
        with patch('notify.logging.getLogger'):
            notify.notify_email(cfg, subject, message)
            
            # Verify SMTP was initialized with right parameters
            mock_smtp.assert_called_once_with("smtp.example.com", 587)
            
            # Verify email was sent
            mock_smtp_instance.sendmail.assert_called_once()

# Tests for config validation
class TestConfiguration:
    def test_validate_config(self):
        # Valid config
        valid_config = {
            "timer": 300,
            "loglevel": "INFO",
            "ip_service": "https://api.ipify.org",
            "providers": [
                {
                    "name": "test_provider",
                    "protocol": "dyndns2",
                    "url": "https://example.com/update",
                    "hostname": "test.example.com",
                    "username": "user",
                    "password": "pass"
                }
            ]
        }
        
        with patch('update_dyndns.log'):
            assert update_dyndns.validate_config(valid_config) is True
    
    def test_validate_invalid_config(self):
        # Provider mit fehlendem erforderlichen Feld
        invalid_config = {
            "timer": 300,
            "providers": [
                {
                    "name": "invalid_provider",
                    # Fehlendes "protocol" Feld - das sollte auf jeden Fall einen Fehler verursachen
                    "url": "https://example.com/update"
                }
            ]
        }
        
        with patch('update_dyndns.log'):
            assert update_dyndns.validate_config(invalid_config) is False

# Test für den Fall, dass keine Benachrichtigungskonfiguration vorhanden ist
def test_send_notifications_with_no_config():
    # Sollte ohne Fehler beendet werden
    with patch('notify.logging.getLogger'):
        notify.send_notifications(None, "ERROR", "Test message")
        # No assertion needed - test passes if no exception is thrown

# Für update_provider Tests sicherstellen, dass config vorhanden ist
@patch('update_dyndns.config', {'notify': {'email': {'enabled': True}}})
def test_update_provider_error_handling():
    provider = {
        "name": "test_provider",
        "protocol": "dyndns2",
        "url": "https://example.com/update",
        "hostname": "test.example.com"
    }
    
    with patch('update_dyndns.log'), patch('update_dyndns.update_dyndns2', return_value=None):
        result = update_dyndns.update_provider(provider, "192.168.1.1")
        assert result is False  # Update should fail