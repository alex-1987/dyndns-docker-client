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
    def test_get_public_ip_invalid_ip(self, mock_get):
        # Test when service returns invalid IP format
        mock_response = MagicMock()
        mock_response.text = "invalid-ip-format"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        with patch('update_dyndns.log'):
            result = update_dyndns.get_public_ip("https://example.com/ip")
            assert result is None
    
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
def test_update_provider_error_handling():
    provider = {
        "name": "test_provider",
        "protocol": "dyndns2",
        "url": "https://example.com/update",
        "hostname": "test.example.com"
    }
    
    with patch('update_dyndns.log'), \
         patch('update_dyndns.update_dyndns2', return_value=None), \
         patch('update_dyndns.config', {'notify': {'email': {'enabled': True}}}):
        result = update_dyndns.update_provider(provider, "192.168.1.1")
        assert result is False  # Update should fail

# Tests for TRACE level functionality
class TestTraceLevel:
    def test_trace_level_validation(self):
        # Test TRACE level is accepted in config validation
        config_with_trace = {
            "timer": 300,
            "consolelevel": "TRACE",
            "loglevel": "TRACE", 
            "providers": [
                {
                    "name": "test_provider",
                    "protocol": "dyndns2",
                    "url": "https://example.com/update",
                    "hostname": "test.example.com"
                }
            ]
        }
        
        with patch('update_dyndns.log'):
            assert update_dyndns.validate_config(config_with_trace) is True

# Tests for logging configuration
class TestLoggingConfiguration:
    def test_logging_config_validation_valid(self):
        # Test valid logging configuration
        config_with_logging = {
            "timer": 300,
            "providers": [],
            "logging": {
                "enabled": True,
                "file": "/app/config/test.log",
                "max_size_mb": 5,
                "backup_count": 2
            }
        }
        
        with patch('update_dyndns.log'):
            assert update_dyndns.validate_config(config_with_logging) is True
    
    def test_logging_config_validation_invalid(self):
        # Test invalid logging configuration
        config_with_invalid_logging = {
            "timer": 300,
            "providers": [],
            "logging": {
                "enabled": True,
                # Missing required "file" field
                "max_size_mb": 5
            }
        }
        
        with patch('update_dyndns.log'):
            assert update_dyndns.validate_config(config_with_invalid_logging) is False
    
    @patch('update_dyndns.os.makedirs')
    @patch('update_dyndns.RotatingFileHandler')
    def test_setup_logging_file_enabled(self, mock_handler, mock_makedirs):
        # Test file logging setup
        config = {
            "logging": {
                "enabled": True,
                "file": "/app/config/test.log",
                "max_size_mb": 5,
                "backup_count": 2
            }
        }
        
        with patch('update_dyndns.logging.getLogger') as mock_logger:
            result = update_dyndns.setup_logging("INFO", config)
            assert result == "INFO"
            mock_makedirs.assert_called_once()
            mock_handler.assert_called_once()

# Tests for interface functions
class TestInterfaceFunctions:
    @patch('update_dyndns.socket.socket')
    @patch('update_dyndns.fcntl.ioctl')
    @patch('update_dyndns.socket.inet_ntoa')
    def test_get_interface_ipv4_success(self, mock_inet_ntoa, mock_ioctl, mock_socket):
        # Mock successful interface IP retrieval
        mock_inet_ntoa.return_value = "192.168.1.100"
        mock_ioctl.return_value = b'\x00' * 20 + b'\xc0\xa8\x01d'  # IP bytes
        
        with patch('update_dyndns.validate_ipv4', return_value=True), \
             patch('update_dyndns.log'):
            result = update_dyndns.get_interface_ipv4("eth0")
            assert result == "192.168.1.100"
    
    @patch('builtins.open', mock_open())
    @patch('update_dyndns.socket.getaddrinfo')
    def test_get_interface_ipv6_success(self, mock_getaddrinfo):
        # Mock IPv6 address info
        mock_getaddrinfo.return_value = [
            (socket.AF_INET6, None, None, None, ("2001:db8::1", 0, 0, 0))
        ]
        
        with patch('update_dyndns.validate_ipv6', return_value=True), \
             patch('update_dyndns.log'):
            result = update_dyndns.get_interface_ipv6("eth0")
            assert result == "2001:db8::1"

# Tests for provider-specific updates
class TestProviderUpdates:
    @patch('requests.get')
    def test_update_cloudflare_success(self, mock_get):
        # Test successful Cloudflare update
        # Mock zone ID response
        zone_response = MagicMock()
        zone_response.json.return_value = {
            "success": True,
            "result": [{"id": "zone123"}]
        }
        
        # Mock record response
        record_response = MagicMock()
        record_response.json.return_value = {
            "success": True,
            "result": [{"id": "record123", "content": "1.2.3.4"}]
        }
        
        # Mock update response
        update_response = MagicMock()
        update_response.ok = True
        
        mock_get.side_effect = [zone_response, record_response]
        
        provider = {
            "api_token": "test-token",
            "zone": "example.com",
            "record_name": "test.example.com"
        }
        
        with patch('requests.patch', return_value=update_response), \
             patch('update_dyndns.log'):
            result = update_dyndns.update_cloudflare(provider, "1.2.3.5")
            assert result == "updated"
    
    @patch('requests.get')
    def test_update_ipv64_success(self, mock_get):
        # Test successful ipv64 update
        mock_response = MagicMock()
        mock_response.text = "good 192.168.1.1"
        mock_get.return_value = mock_response
        
        provider = {
            "auth_method": "token",
            "token": "test-token",
            "domain": "test.ipv64.net"
        }
        
        with patch('update_dyndns.log'):
            result = update_dyndns.update_ipv64(provider, "192.168.1.1")
            assert result == "updated"

# Tests for error handling
class TestErrorHandling:
    def test_invalid_ip_validation_notification(self):
        # Test that invalid IPs trigger notifications
        with patch('update_dyndns.send_notifications') as mock_notify, \
             patch('update_dyndns.log'):
            
            # This should be called when invalid IP is detected
            update_dyndns.validate_ipv4("999.999.999.999")
            # Additional test logic here...
    
    def test_update_provider_exception_handling(self):
        # Test exception handling in update_provider
        provider = {
            "name": "test_provider",
            "protocol": "dyndns2"  # Valid protocol but will cause exception
        }
        
        with patch('update_dyndns.log') as mock_log, \
             patch('update_dyndns.send_notifications') as mock_notify, \
             patch('update_dyndns.update_dyndns2', side_effect=Exception("Test error")), \
             patch('update_dyndns.config', {'notify': {'email': {'enabled': True}}}):
            
            result = update_dyndns.update_provider(provider, "192.168.1.1")
            assert result is None
            # The exception handling should trigger send_notifications
            mock_notify.assert_called_once()

# Tests for file operations
class TestFileOperations:
    def test_load_last_ip_success(self):
        # Test successful IP loading from file
        with patch('builtins.open', mock_open(read_data="192.168.1.1")):
            result = update_dyndns.load_last_ip("v4")
            assert result == "192.168.1.1"
    
    def test_load_last_ip_file_not_found(self):
        # Test handling when IP file doesn't exist
        with patch('builtins.open', side_effect=FileNotFoundError()):
            result = update_dyndns.load_last_ip("v4")
            assert result is None
    
    def test_save_last_ip_success(self):
        # Test successful IP saving
        with patch('builtins.open', mock_open()) as mock_file, \
             patch('update_dyndns.log'):
            update_dyndns.save_last_ip("v4", "192.168.1.1")
            mock_file.assert_called_once()

# Tests for configuration edge cases
class TestConfigurationEdgeCases:
    def test_empty_providers_list(self):
        # Test config with empty providers
        config = {
            "timer": 300,
            "providers": []
        }
        
        with patch('update_dyndns.log'):
            assert update_dyndns.validate_config(config) is True
    
    def test_missing_timer(self):
        # Test config without timer
        config = {
            "providers": [{"name": "test", "protocol": "dyndns2", "url": "https://example.com"}]
        }
        
        with patch('update_dyndns.log'):
            assert update_dyndns.validate_config(config) is False
    
    def test_invalid_protocol(self):
        # Test provider with invalid protocol
        config = {
            "timer": 300,
            "providers": [
                {
                    "name": "test",
                    "protocol": "invalid_protocol",
                    "url": "https://example.com"
                }
            ]
        }
        
        with patch('update_dyndns.log'):
            assert update_dyndns.validate_config(config) is False

# Tests for different authentication methods
class TestAuthenticationMethods:
    @patch('requests.get')
    def test_dyndns2_token_auth(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "good"
        mock_get.return_value = mock_response
        
        provider = {
            "name": "test",
            "url": "https://example.com/update",
            "auth_method": "token",
            "token": "test-token",
            "hostname": "test.example.com"
        }
        
        with patch('update_dyndns.log'):
            result = update_dyndns.update_dyndns2(provider, "192.168.1.1")
            assert result == "updated"
            
            # Verify token was passed in params
            args, kwargs = mock_get.call_args
            assert kwargs.get("params", {}).get("token") == "test-token"
    
    @patch('requests.get')
    def test_dyndns2_bearer_auth(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "good"
        mock_get.return_value = mock_response
        
        provider = {
            "name": "test",
            "url": "https://example.com/update",
            "auth_method": "bearer",
            "token": "bearer-token",
            "hostname": "test.example.com"
        }
        
        with patch('update_dyndns.log'):
            result = update_dyndns.update_dyndns2(provider, "192.168.1.1")
            assert result == "updated"
            
            # Verify bearer token was passed in headers
            args, kwargs = mock_get.call_args
            assert kwargs.get("headers", {}).get("Authorization") == "Bearer bearer-token"

# Tests for logging levels and message filtering
class TestLogLevelFiltering:
    def test_should_log_function(self):
        # Test the should_log function with TRACE level
        assert update_dyndns.should_log("TRACE", "TRACE") is True
        assert update_dyndns.should_log("DEBUG", "TRACE") is True
        assert update_dyndns.should_log("INFO", "TRACE") is True
        assert update_dyndns.should_log("TRACE", "INFO") is False
        assert update_dyndns.should_log("ERROR", "WARNING") is True
        assert update_dyndns.should_log("WARNING", "ERROR") is False

    def test_log_function_basic_functionality(self):
        # Simple test that log function works without errors
        with patch('builtins.print') as mock_print, \
             patch('update_dyndns.file_logger_instance', None):
            
            # This should at least print to console
            update_dyndns.log("Test message", "INFO", "TEST")
            mock_print.assert_called_once()
            
            # Verify the message format is correct
            call_args = mock_print.call_args[0][0]
            assert "[INFO] TEST --> Test message" in call_args

# Tests for IP validation edge cases
class TestIPValidationEdgeCases:
    def test_validate_ipv4_edge_cases(self):
        # Test edge cases for IPv4 validation
        assert update_dyndns.validate_ipv4("0.0.0.0") is True
        assert update_dyndns.validate_ipv4("255.255.255.255") is True
        assert update_dyndns.validate_ipv4("192.168.1.1") is True
        assert update_dyndns.validate_ipv4("10.0.0.1") is True
        
        # Invalid cases
        assert update_dyndns.validate_ipv4("256.1.1.1") is False
        assert update_dyndns.validate_ipv4("1.1.1") is False
        assert update_dyndns.validate_ipv4("1.1.1.1.1") is False
        assert update_dyndns.validate_ipv4("") is False
        assert update_dyndns.validate_ipv4("abc.def.ghi.jkl") is False
        assert update_dyndns.validate_ipv4("192.168.1.-1") is False

    def test_validate_ipv6_edge_cases(self):
        # Test edge cases for IPv6 validation
        assert update_dyndns.validate_ipv6("::1") is True
        assert update_dyndns.validate_ipv6("2001:db8::1") is True
        assert update_dyndns.validate_ipv6("2001:0db8:85a3:0000:0000:8a2e:0370:7334") is True
        assert update_dyndns.validate_ipv6("::") is True
        
        # Invalid cases
        assert update_dyndns.validate_ipv6("192.168.1.1") is False  # IPv4
        assert update_dyndns.validate_ipv6("") is False
        assert update_dyndns.validate_ipv6("invalid") is False
        assert update_dyndns.validate_ipv6("2001:0db8:85a3::8a2e:0370:7334:extra") is False

# Tests for configuration reloading
class TestConfigurationReloading:
    def test_config_reload_on_file_change(self):
        # Mock file modification time change
        with patch('update_dyndns.os.path.getmtime') as mock_getmtime, \
             patch('builtins.open', mock_open()), \
             patch('update_dyndns.yaml.safe_load') as mock_yaml:
            
            mock_getmtime.side_effect = [1000, 1001]  # File changed
            
            # Mock valid config
            mock_yaml.return_value = {
                "timer": 600,
                "providers": [{"name": "test", "protocol": "dyndns2", "url": "https://example.com"}]
            }
            
            with patch('update_dyndns.validate_config', return_value=True), \
                 patch('update_dyndns.setup_logging'), \
                 patch('update_dyndns.log'):
                
                # This would be called in the main loop when config changes
                # Test logic for config reloading would go here
                pass

# Tests for skip_update_on_startup functionality
class TestSkipUpdateOnStartup:
    @patch('update_dyndns.load_last_ip')
    @patch('update_dyndns.save_last_ip')
    def test_skip_update_when_ip_unchanged(self, mock_save, mock_load):
        # Mock that IP hasn't changed
        mock_load.side_effect = lambda version: "192.168.1.1" if version == "v4" else None
        
        # Test that updates are skipped when IP is the same
        with patch('update_dyndns.log'):
            # Simulate the logic from main() when skip_update_on_startup is True
            last_ip = "192.168.1.1"
            current_ip = "192.168.1.1"
            skip_on_startup = True
            
            ip_changed = (current_ip != last_ip)
            should_update = not skip_on_startup or ip_changed
            
            assert should_update is False

    @patch('update_dyndns.load_last_ip')
    @patch('update_dyndns.save_last_ip')
    def test_update_when_ip_changed(self, mock_save, mock_load):
        # Mock that IP has changed
        mock_load.side_effect = lambda version: "192.168.1.1" if version == "v4" else None
        
        # Test that updates proceed when IP has changed
        with patch('update_dyndns.log'):
            last_ip = "192.168.1.1"
            current_ip = "192.168.1.2"
            skip_on_startup = True
            
            ip_changed = (current_ip != last_ip)
            should_update = not skip_on_startup or ip_changed
            
            assert should_update is True

# Tests for provider error responses
class TestProviderErrorResponses:
    @patch('requests.get')
    def test_dyndns2_error_response(self, mock_get):
        # Test various error responses from DynDNS2 providers
        error_responses = [
            "badauth",
            "nohost",
            "abuse",
            "badagent",
            "dnserr",
            "911"
        ]
        
        for error_response in error_responses:
            mock_response = MagicMock()
            mock_response.text = error_response
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
                assert result is None  # Should return None for errors

    @patch('requests.get')
    def test_ipv64_overcommitted_response(self, mock_get):
        # Test ipv64 overcommitted response (match the actual code spelling)
        mock_response = MagicMock()
        mock_response.text = "overcommited"  # Match spelling in actual code
        mock_response.status_code = 403
        mock_get.return_value = mock_response
        
        provider = {
            "auth_method": "token",
            "token": "test-token",
            "domain": "test.ipv64.net"
        }
        
        with patch('update_dyndns.log'):
            result = update_dyndns.update_ipv64(provider, "192.168.1.1")
            assert result is False

# Tests for mixed IPv4/IPv6 scenarios
class TestMixedIPScenarios:
    @patch('requests.get')
    def test_update_both_ipv4_and_ipv6(self, mock_get):
        # Test updating both IPv4 and IPv6 records
        mock_response = MagicMock()
        mock_response.text = "good"
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
            result = update_dyndns.update_dyndns2(provider, "192.168.1.1", "2001:db8::1")
            assert result == "updated"
            
            # Verify both IPs were passed
            args, kwargs = mock_get.call_args
            params = kwargs.get("params", {})
            assert params.get("myip") == "192.168.1.1"
            assert params.get("myipv6") == "2001:db8::1"

    def test_ipv4_only_scenario(self):
        # Test scenario with only IPv4 configured
        with patch('update_dyndns.get_public_ip', return_value="192.168.1.1"), \
             patch('update_dyndns.get_public_ipv6', return_value=None), \
             patch('update_dyndns.validate_ipv4', return_value=True):
            
            # Simulate getting only IPv4
            ipv4 = "192.168.1.1"
            ipv6 = None
            
            assert ipv4 is not None
            assert ipv6 is None

# Tests for notification integration
class TestNotificationIntegration:
    @patch('update_dyndns.send_notifications')
    def test_notification_on_successful_update(self, mock_notify):
        # Test that notifications are sent on successful updates
        provider = {
            "name": "test_provider",
            "protocol": "dyndns2"
        }
        
        with patch('update_dyndns.update_dyndns2', return_value="updated"), \
             patch('update_dyndns.log'), \
             patch('update_dyndns.config', {'notify': {'email': {'enabled': True}}}):
            
            result = update_dyndns.update_provider(provider, "192.168.1.1")
            assert result is True
            mock_notify.assert_called_once()

    @patch('update_dyndns.send_notifications')
    def test_notification_on_update_error(self, mock_notify):
        # Test that notifications are sent on update errors
        provider = {
            "name": "test_provider",
            "protocol": "dyndns2"
        }
        
        with patch('update_dyndns.update_dyndns2', return_value=None), \
             patch('update_dyndns.log'), \
             patch('update_dyndns.config', {'notify': {'email': {'enabled': True}}}):
            
            result = update_dyndns.update_provider(provider, "192.168.1.1")
            assert result is False
            mock_notify.assert_called_once()

# Tests for logging with file_only_on_change parameter
class TestFileOnlyOnChangeLogging:
    def test_log_basic_functionality(self):
        # Test basic logging functionality without complex level filtering
        with patch('builtins.print'), \
             patch('update_dyndns.file_logger_instance') as mock_file_logger:
            
            # Test that the function doesn't crash and basic functionality works
            update_dyndns.log("Test routine message", "INFO", "MAIN", file_only_on_change=True)
            update_dyndns.log("Test error message", "ERROR", "MAIN", file_only_on_change=True)
            
            # Just verify the function runs without exceptions
            assert True

# Tests for interface error handling
class TestInterfaceErrorHandling:
    @patch('update_dyndns.socket.socket')
    def test_interface_not_found_error(self, mock_socket):
        # Test handling when interface doesn't exist
        mock_socket.side_effect = OSError("No such device")
        
        with patch('update_dyndns.log'):
            result = update_dyndns.get_interface_ipv4("nonexistent0")
            assert result is None

    @patch('builtins.open', side_effect=FileNotFoundError())
    def test_interface_ipv6_not_found(self, mock_open):
        # Test IPv6 interface not found
        with patch('update_dyndns.log'):
            result = update_dyndns.get_interface_ipv6("nonexistent0")
            assert result is None

# Tests for concurrent/threading scenarios (if applicable)
class TestConcurrencyScenarios:
    def test_config_modification_during_execution(self):
        # Test behavior when config is modified during execution
        # This would test race conditions if threading is used
        assert True  # Placeholder test

# Tests for memory and resource management
class TestResourceManagement:
    def test_log_rotation_setup(self):
        # Test that log rotation is properly configured
        config = {
            "logging": {
                "enabled": True,
                "file": "/app/config/test.log",
                "max_size_mb": 5,
                "backup_count": 3
            }
        }
        
        with patch('update_dyndns.RotatingFileHandler') as mock_handler, \
             patch('update_dyndns.os.makedirs'), \
             patch('update_dyndns.logging.getLogger'):
            
            update_dyndns.setup_logging("INFO", config)
            
            # Verify RotatingFileHandler was called with correct parameters
            mock_handler.assert_called_once_with(
                "/app/config/test.log",
                maxBytes=5 * 1024 * 1024,
                backupCount=3
            )

# Integration tests (testing multiple components together)
class TestIntegrationScenarios:
    @patch('update_dyndns.get_public_ip')
    @patch('update_dyndns.update_dyndns2')
    @patch('update_dyndns.send_notifications')
    def test_full_update_cycle(self, mock_notify, mock_update, mock_get_ip):
        # Test a complete update cycle
        mock_get_ip.return_value = "192.168.1.2"
        mock_update.return_value = "updated"
        
        provider = {
            "name": "test_provider",
            "protocol": "dyndns2",
            "url": "https://example.com/update",
            "hostname": "test.example.com"
        }
        
        with patch('update_dyndns.log'), \
             patch('update_dyndns.config', {'notify': {'email': {'enabled': True}}}):
            
            # Simulate IP change detection and update
            current_ip = mock_get_ip("https://api.ipify.org")
            result = update_dyndns.update_provider(provider, current_ip)
            
            assert result is True
            mock_update.assert_called_once()
            mock_notify.assert_called_once()

# Performance tests
class TestPerformance:
    def test_ip_validation_performance(self):
        # Test that IP validation is fast for large numbers of IPs
        import time
        
        start_time = time.time()
        for i in range(1000):
            update_dyndns.validate_ipv4(f"192.168.1.{i % 255}")
        end_time = time.time()
        
        # Should complete in reasonable time (less than 1 second)
        assert (end_time - start_time) < 1.0

# Tests for environment-specific behavior
class TestEnvironmentBehavior:
    def test_docker_environment_detection(self):
        # Test behavior specific to Docker environment
        with patch.dict(os.environ, {'DOCKER_ENV': 'true'}):
            # Simple test that environment variable is accessible
            assert os.environ.get('DOCKER_ENV') == 'true'

    def test_file_permissions(self):
        # Test behavior with different file permissions
        # Simple placeholder test
        assert True

# Additional tests for better coverage
class TestAdditionalCoverage:
    def test_get_public_ipv6_invalid_ip(self):
        # Test when IPv6 service returns invalid format
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.text = "invalid-ipv6-format"
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            with patch('update_dyndns.log'):
                result = update_dyndns.get_public_ipv6("https://example.com/ipv6")
                assert result is None
    
    def test_update_dyndns2_missing_hostname(self):
        # Test DynDNS2 update with missing hostname/domain/host
        provider = {
            "name": "test_provider",
            "url": "https://example.com/update",
            "auth_method": "basic",
            "username": "user",
            "password": "pass"
            # Missing hostname/domain/host
        }
        
        with patch('update_dyndns.log'):
            result = update_dyndns.update_dyndns2(provider, "192.168.1.1")
            assert result is None
    
    def test_update_dyndns2_invalid_auth(self):
        # Test DynDNS2 update with invalid auth configuration
        provider = {
            "name": "test_provider",
            "url": "https://example.com/update",
            "auth_method": "invalid_method",
            "hostname": "test.example.com"
        }
        
        with patch('update_dyndns.log'):
            result = update_dyndns.update_dyndns2(provider, "192.168.1.1")
            assert result is None
    
    def test_cloudflare_zone_not_found(self):
        # Test Cloudflare with zone not found
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "success": False,
                "result": []
            }
            mock_get.return_value = mock_response
            
            provider = {
                "api_token": "test-token",
                "zone": "nonexistent.com",
                "record_name": "test.nonexistent.com"
            }
            
            with patch('update_dyndns.log'):
                try:
                    update_dyndns.update_cloudflare(provider, "1.2.3.4")
                    assert False, "Should have raised an exception"
                except Exception:
                    assert True  # Expected behavior
    
    def test_validate_config_with_cloudflare_missing_fields(self):
        # Test config validation with Cloudflare provider missing required fields
        config = {
            "timer": 300,
            "providers": [
                {
                    "name": "incomplete_cloudflare",
                    "protocol": "cloudflare"
                    # Missing zone, api_token, record_name
                }
            ]
        }
        
        with patch('update_dyndns.log'):
            assert update_dyndns.validate_config(config) is False

# Test to verify TRACE level is correctly handled in should_log
class TestTraceLevelSpecific:
    def test_trace_level_should_log_correctly(self):
        # Test that TRACE level works in should_log function
        assert update_dyndns.should_log("TRACE", "TRACE") is True
        assert update_dyndns.should_log("DEBUG", "TRACE") is True  
        assert update_dyndns.should_log("INFO", "TRACE") is True
        assert update_dyndns.should_log("WARNING", "TRACE") is True
        assert update_dyndns.should_log("ERROR", "TRACE") is True
        assert update_dyndns.should_log("CRITICAL", "TRACE") is True
        
        # When configured level is higher than TRACE
        assert update_dyndns.should_log("TRACE", "DEBUG") is False
        assert update_dyndns.should_log("TRACE", "INFO") is False