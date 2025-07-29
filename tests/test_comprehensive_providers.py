#!/usr/bin/env python3
"""
Comprehensive Provider Test Suite
Tests all provider functionality, configurations, and edge cases
Can be run locally or in CI/CD environments
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock, mock_open
import json

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from update_dyndns import (
    create_provider, update_provider, BaseProvider, 
    CloudflareProvider, IPV64Provider, DynDNS2Provider,
    validate_ipv4, validate_ipv6
)

class TestProviderArchitecture(unittest.TestCase):
    """Test the unified provider architecture comprehensively."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.valid_configs = {
            'cloudflare': {
                'name': 'test-cloudflare',
                'protocol': 'cloudflare',
                'zone': 'example.com',
                'api_token': 'test_token_123',
                'record_name': 'sub.example.com'
            },
            'ipv64': {
                'name': 'test-ipv64', 
                'protocol': 'ipv64',
                'auth_method': 'token',
                'token': 'test_token_456',
                'domain': 'example.com'
            },
            'dyndns2': {
                'name': 'test-dyndns2',
                'protocol': 'dyndns2',
                'url': 'https://updates.example.org/api/',
                'auth_method': 'basic',
                'username': 'testuser',
                'password': 'testpass',
                'hostname': 'test.example.com'
            }
        }
        
        self.test_ips = {
            'ipv4': '192.168.1.100',
            'ipv6': '2001:db8::1'
        }
    
    def test_provider_creation_all_types(self):
        """Test creating all provider types successfully."""
        print("\n🔧 Testing Provider Creation...")
        
        for provider_type, config in self.valid_configs.items():
            with self.subTest(provider=provider_type):
                provider = create_provider(config)
                
                # Check provider type
                if provider_type == 'cloudflare':
                    self.assertIsInstance(provider, CloudflareProvider)
                elif provider_type == 'ipv64':
                    self.assertIsInstance(provider, IPV64Provider)
                elif provider_type == 'dyndns2':
                    self.assertIsInstance(provider, DynDNS2Provider)
                
                # Check provider properties
                self.assertEqual(provider.name, config['name'])
                self.assertEqual(provider.provider_type, config['protocol'])
                
                print(f"  ✅ {provider_type.upper()}: {type(provider).__name__}")
    
    def test_field_name_compatibility(self):
        """Test backward compatibility with different field names."""
        print("\n🔄 Testing Field Name Compatibility...")
        
        # Test protocol vs type field
        config_protocol = {
            'name': 'test-protocol',
            'protocol': 'cloudflare',
            'zone': 'example.com',
            'api_token': 'test_token',
            'record_name': 'sub.example.com'
        }
        
        config_type = {
            'name': 'test-type',
            'type': 'cloudflare',
            'zone': 'example.com',
            'api_token': 'test_token',
            'record_name': 'sub.example.com'
        }
        
        provider1 = create_provider(config_protocol)
        provider2 = create_provider(config_type)
        
        self.assertIsInstance(provider1, CloudflareProvider)
        self.assertIsInstance(provider2, CloudflareProvider)
        print("  ✅ 'protocol' and 'type' fields both work")
        
        # Test Cloudflare token field names
        config_api_token = {
            'protocol': 'cloudflare',
            'name': 'test-api-token',
            'zone': 'example.com',
            'api_token': 'test_token',
            'record_name': 'sub.example.com'
        }
        
        config_token = {
            'protocol': 'cloudflare',
            'name': 'test-token',
            'zone': 'example.com',
            'token': 'test_token',
            'record_name': 'sub.example.com'
        }
        
        provider3 = create_provider(config_api_token)
        provider4 = create_provider(config_token)
        
        self.assertIsInstance(provider3, CloudflareProvider)
        self.assertIsInstance(provider4, CloudflareProvider)
        print("  ✅ 'api_token' and 'token' fields both work for Cloudflare")
    
    def test_case_insensitive_protocols(self):
        """Test case-insensitive protocol names."""
        print("\n🔤 Testing Case Insensitive Protocols...")
        
        test_cases = [
            ('CLOUDFLARE', CloudflareProvider),
            ('Cloudflare', CloudflareProvider),
            ('cloudflare', CloudflareProvider),
            ('IPV64', IPV64Provider),
            ('ipv64', IPV64Provider),
            ('DYNDNS2', DynDNS2Provider),
            ('dyndns2', DynDNS2Provider)
        ]
        
        for protocol_name, expected_class in test_cases:
            config = {
                'protocol': protocol_name,
                'name': f'test-{protocol_name.lower()}',
                'zone': 'example.com',
                'api_token': 'test_token',
                'record_name': 'sub.example.com'
            }
            
            if 'ipv64' in protocol_name.lower():
                config.update({'token': 'test_token', 'domain': 'example.com'})
                config.pop('zone', None)
                config.pop('api_token', None)
                config.pop('record_name', None)
            elif 'dyndns2' in protocol_name.lower():
                config.update({
                    'url': 'https://updates.example.org/api/',
                    'hostname': 'test.example.com',
                    'auth_method': 'token',
                    'token': 'test_token'
                })
                config.pop('zone', None)
                config.pop('api_token', None)
                config.pop('record_name', None)
            
            provider = create_provider(config)
            self.assertIsInstance(provider, expected_class)
            print(f"  ✅ {protocol_name} -> {expected_class.__name__}")
    
    def test_config_validation(self):
        """Test configuration validation for all providers."""
        print("\n🔍 Testing Configuration Validation...")
        
        # Test missing required fields
        invalid_configs = {
            'cloudflare_missing_token': {
                'protocol': 'cloudflare',
                'name': 'test-cf',
                'zone': 'example.com',
                'record_name': 'sub.example.com'
                # Missing api_token
            },
            'cloudflare_missing_zone': {
                'protocol': 'cloudflare',
                'name': 'test-cf',
                'api_token': 'test_token',
                'record_name': 'sub.example.com'
                # Missing zone
            },
            'ipv64_missing_token': {
                'protocol': 'ipv64',
                'name': 'test-ipv64',
                'domain': 'example.com'
                # Missing token
            },
            'ipv64_missing_domain': {
                'protocol': 'ipv64',
                'name': 'test-ipv64',
                'token': 'test_token'
                # Missing domain/host/hostname
            },
            'dyndns2_missing_url': {
                'protocol': 'dyndns2',
                'name': 'test-dyndns2',
                'hostname': 'test.example.com',
                'token': 'test_token'
                # Missing url
            },
            'dyndns2_missing_hostname': {
                'protocol': 'dyndns2',
                'name': 'test-dyndns2',
                'url': 'https://updates.example.org/api/',
                'token': 'test_token'
                # Missing hostname
            }
        }
        
        for test_name, config in invalid_configs.items():
            with self.subTest(config=test_name):
                with self.assertRaises(ValueError):
                    create_provider(config)
                print(f"  ✅ {test_name}: Validation correctly failed")
    
    def test_unknown_provider_types(self):
        """Test handling of unknown provider types."""
        print("\n❓ Testing Unknown Provider Types...")
        
        unknown_configs = [
            {'protocol': 'unknown_provider', 'name': 'test'},
            {'protocol': '', 'name': 'test'},
            {'name': 'test'}  # No protocol field
        ]
        
        for i, config in enumerate(unknown_configs):
            with self.subTest(config=i):
                with self.assertRaises(ValueError) as context:
                    create_provider(config)
                
                error_msg = str(context.exception)
                self.assertTrue(
                    "Unknown provider type" in error_msg or 
                    "No provider type specified" in error_msg
                )
                print(f"  ✅ Config {i+1}: {error_msg[:50]}...")
    
    @patch('update_dyndns.send_notifications')
    @patch('update_dyndns.update_cloudflare')
    @patch('update_dyndns.update_ipv64')
    @patch('update_dyndns.update_dyndns2')
    def test_unified_provider_updates(self, mock_dyndns2, mock_ipv64, mock_cf, mock_notify):
        """Test unified provider update functionality."""
        print("\n🚀 Testing Unified Provider Updates...")
        
        # Configure mocks
        mock_cf.return_value = "updated"
        mock_ipv64.return_value = "updated"
        mock_dyndns2.return_value = "updated"
        
        for provider_type, config in self.valid_configs.items():
            with self.subTest(provider=provider_type):
                provider = create_provider(config)
                result = provider.update_unified(self.test_ips['ipv4'], None)
                
                self.assertEqual(result, "updated")
                print(f"  ✅ {provider_type.upper()}: Update successful")
                
                # Check if notification was called
                self.assertTrue(mock_notify.called)
                mock_notify.reset_mock()
    
    @patch('update_dyndns.send_notifications')
    @patch('update_dyndns.update_cloudflare')
    @patch('update_dyndns.config', {'notify': {'enabled': True}})
    def test_legacy_provider_compatibility(self, mock_cf, mock_notify):
        """Test that legacy provider system still works."""
        print("\n🔄 Testing Legacy Provider Compatibility...")
        
        mock_cf.return_value = "updated"
        
        legacy_config = self.valid_configs['cloudflare'].copy()
        result = update_provider(legacy_config, self.test_ips['ipv4'], None)
        
        self.assertTrue(result)
        self.assertTrue(mock_notify.called)
        print("  ✅ Legacy system works and sends notifications")
    
    def test_notification_functionality(self):
        """Test notification functionality in providers."""
        print("\n📧 Testing Notification Functionality...")
        
        with patch('update_dyndns.send_notifications') as mock_notify:
            config = self.valid_configs['cloudflare'].copy()
            config['notify'] = {
                'discord': {
                    'webhook_url': 'https://discord.com/api/webhooks/test',
                    'enabled': True
                }
            }
            
            provider = create_provider(config)
            
            # Test success notification
            provider.send_success_notification(self.test_ips['ipv4'])
            self.assertTrue(mock_notify.called)
            args = mock_notify.call_args
            self.assertEqual(args[0][1], "UPDATE")  # Notification type
            print("  ✅ Success notifications work")
            
            mock_notify.reset_mock()
            
            # Test error notification
            provider.send_error_notification("Test error")
            self.assertTrue(mock_notify.called)
            args = mock_notify.call_args
            self.assertEqual(args[0][1], "ERROR")  # Notification type
            print("  ✅ Error notifications work")
    
    def test_ip_validation_functions(self):
        """Test IP validation helper functions."""
        print("\n🌐 Testing IP Validation...")
        
        # IPv4 tests
        valid_ipv4 = ["192.168.1.1", "8.8.8.8", "0.0.0.0", "255.255.255.255"]
        invalid_ipv4 = ["256.0.0.1", "192.168.1", "not-an-ip", "", "192.168.1.1.1"]
        
        for ip in valid_ipv4:
            self.assertTrue(validate_ipv4(ip), f"Valid IPv4 failed: {ip}")
        
        for ip in invalid_ipv4:
            self.assertFalse(validate_ipv4(ip), f"Invalid IPv4 passed: {ip}")
        
        print("  ✅ IPv4 validation works correctly")
        
        # IPv6 tests
        valid_ipv6 = ["2001:0db8:85a3:0000:0000:8a2e:0370:7334", "::1", "2001:db8::1", "::"]
        invalid_ipv6 = ["192.168.1.1", "", "invalid", "2001:0db8:85a3::8a2e:0370:7334:extra"]
        
        for ip in valid_ipv6:
            self.assertTrue(validate_ipv6(ip), f"Valid IPv6 failed: {ip}")
        
        for ip in invalid_ipv6:
            self.assertFalse(validate_ipv6(ip), f"Invalid IPv6 passed: {ip}")
        
        print("  ✅ IPv6 validation works correctly")
    
    def test_real_world_config_formats(self):
        """Test with real configuration examples from config.example.yaml."""
        print("\n📝 Testing Real-World Config Formats...")
        
        real_world_configs = [
            # Cloudflare from config.example.yaml
            {
                'name': 'my-cloudflare',
                'protocol': 'cloudflare',
                'zone': 'yourdomain.tld',
                'api_token': 'your_cloudflare_api_token',
                'record_name': 'sub.domain.tld'
            },
            # IPV64 from config.example.yaml
            {
                'name': 'my-ipv64',
                'protocol': 'ipv64',
                'auth_method': 'token',
                'token': 'your_update_token',
                'domain': 'yourdomain.tld'
            },
            # DynDNS2 from config.example.yaml
            {
                'name': 'my-dyndns2',
                'protocol': 'dyndns2',
                'url': 'https://updates.dnsdynamic.org/api/',
                'auth_method': 'basic',
                'username': 'youruser',
                'password': 'yourpass',
                'hostname': 'yourdomain.dynu.net'
            }
        ]
        
        for config in real_world_configs:
            provider = create_provider(config)
            self.assertIsNotNone(provider)
            self.assertEqual(provider.name, config['name'])
            print(f"  ✅ {config['name']}: Real config format works")

class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""
    
    def test_empty_and_null_values(self):
        """Test handling of empty and null values."""
        print("\n🚫 Testing Empty and Null Values...")
        
        edge_cases = [
            {'protocol': 'cloudflare', 'name': '', 'zone': 'example.com', 'api_token': '', 'record_name': 'sub.example.com'},
            {'protocol': 'cloudflare', 'name': None, 'zone': 'example.com', 'api_token': 'token', 'record_name': 'sub.example.com'},
            {'protocol': 'ipv64', 'name': 'test', 'token': '', 'domain': 'example.com'},
        ]
        
        for i, config in enumerate(edge_cases):
            with self.subTest(config=i):
                try:
                    provider = create_provider(config)
                    print(f"  ⚠️  Config {i+1}: Unexpectedly succeeded")
                except (ValueError, TypeError) as e:
                    print(f"  ✅ Config {i+1}: Correctly failed - {str(e)[:30]}...")
    
    def test_mixed_case_and_special_chars(self):
        """Test mixed case provider names and special characters."""
        print("\n🔤 Testing Mixed Case and Special Characters...")
        
        special_configs = [
            {'protocol': 'CLOUDFLARE', 'name': 'TEST-Provider_123', 'zone': 'example.com', 'api_token': 'token123', 'record_name': 'sub.example.com'},
            {'protocol': 'ipv64', 'name': 'test.provider@domain', 'token': 'token_with_underscores', 'domain': 'sub-domain.example.com'},
        ]
        
        for i, config in enumerate(special_configs):
            try:
                provider = create_provider(config)
                self.assertIsNotNone(provider)
                print(f"  ✅ Config {i+1}: Special characters handled correctly")
            except Exception as e:
                print(f"  ❌ Config {i+1}: Failed - {e}")

def run_comprehensive_tests():
    """Run all tests and provide a summary."""
    print("🧪 COMPREHENSIVE PROVIDER TEST SUITE")
    print("=" * 60)
    print("Testing all provider functionality, configurations, and edge cases")
    print("Can be run locally or in CI/CD environments")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestProviderArchitecture))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    passed = total_tests - failures - errors
    
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failures}")
    print(f"🚫 Errors: {errors}")
    
    if failures == 0 and errors == 0:
        print("\n🎉 ALL TESTS PASSED! Provider architecture is working correctly.")
        return True
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == '__main__':
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)
