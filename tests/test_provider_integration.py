#!/usr/bin/env python3
"""
Integration tests for Provider Unification System
Tests real configuration formats to prevent field name mismatches
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from update_dyndns import create_provider, BaseProvider, CloudflareProvider, IPV64Provider, DynDNS2Provider

class TestProviderIntegration(unittest.TestCase):
    """Tests provider creation and configuration using real config formats."""
    
    def test_create_provider_with_protocol_field(self):
        """Test provider creation using 'protocol' field (actual config format)."""
        
        # Test Cloudflare with protocol field
        cloudflare_config = {
            'protocol': 'cloudflare',
            'name': 'test-cloudflare',
            'zone': 'example.com',
            'api_token': 'test_token',
            'record_name': 'sub.example.com'
        }
        
        provider = create_provider(cloudflare_config)
        self.assertIsInstance(provider, CloudflareProvider)
        self.assertEqual(provider.name, 'test-cloudflare')
        
        # Test IPV64 with protocol field
        ipv64_config = {
            'protocol': 'ipv64',
            'name': 'test-ipv64',
            'token': 'test_token',
            'domain': 'example.com'
        }
        
        provider = create_provider(ipv64_config)
        self.assertIsInstance(provider, IPV64Provider)
        self.assertEqual(provider.name, 'test-ipv64')
        
        # Test DynDNS2 with protocol field
        dyndns2_config = {
            'protocol': 'dyndns2',
            'name': 'test-dyndns2',
            'url': 'https://updates.dnsdynamic.org/api/',
            'hostname': 'example.com',
            'auth_method': 'token',
            'token': 'test_token'
        }
        
        provider = create_provider(dyndns2_config)
        self.assertIsInstance(provider, DynDNS2Provider)
        self.assertEqual(provider.name, 'test-dyndns2')
    
    def test_create_provider_with_type_field_backward_compatibility(self):
        """Test provider creation using 'type' field for backward compatibility."""
        
        config = {
            'type': 'cloudflare',
            'name': 'test-cloudflare',
            'zone': 'example.com',
            'api_token': 'test_token',
            'record_name': 'sub.example.com'
        }
        
        provider = create_provider(config)
        self.assertIsInstance(provider, CloudflareProvider)
        self.assertEqual(provider.name, 'test-cloudflare')
    
    def test_create_provider_missing_type_protocol(self):
        """Test provider creation fails when neither 'type' nor 'protocol' is specified."""
        
        config = {
            'name': 'test-provider',
            'api_token': 'test_token'
        }
        
        with self.assertRaises(ValueError) as context:
            create_provider(config)
        
        self.assertIn("No provider type specified", str(context.exception))
        self.assertIn("Available types:", str(context.exception))
    
    def test_create_provider_unknown_type(self):
        """Test provider creation fails with unknown provider type."""
        
        config = {
            'protocol': 'unknown_provider',
            'name': 'test-provider'
        }
        
        with self.assertRaises(ValueError) as context:
            create_provider(config)
        
        self.assertIn("Unknown provider type: 'unknown_provider'", str(context.exception))
        self.assertIn("Available types:", str(context.exception))
    
    def test_cloudflare_api_token_field_names(self):
        """Test Cloudflare provider supports both 'api_token' and 'token' field names."""
        
        # Test with api_token (actual config format)
        config1 = {
            'protocol': 'cloudflare',
            'name': 'test-cf1',
            'zone': 'example.com',
            'api_token': 'test_token_1',
            'record_name': 'sub.example.com'
        }
        
        provider1 = create_provider(config1)
        self.assertIsInstance(provider1, CloudflareProvider)
        
        # Test with token (backward compatibility)
        config2 = {
            'protocol': 'cloudflare',
            'name': 'test-cf2',
            'zone': 'example.com',
            'token': 'test_token_2',  # Alternative field name
            'record_name': 'sub.example.com'
        }
        
        provider2 = create_provider(config2)
        self.assertIsInstance(provider2, CloudflareProvider)
    
    def test_real_config_formats_from_example(self):
        """Test with exact config formats from config.example.yaml."""
        
        # Exact Cloudflare config from example
        cloudflare_config = {
            'name': 'my-cloudflare',
            'protocol': 'cloudflare',
            'zone': 'yourdomain.tld',
            'api_token': 'your_cloudflare_api_token',
            'record_name': 'sub.domain.tld'
        }
        
        provider = create_provider(cloudflare_config)
        self.assertIsInstance(provider, CloudflareProvider)
        self.assertEqual(provider.name, 'my-cloudflare')
        
        # Exact IPV64 config from example
        ipv64_config = {
            'name': 'my-ipv64',
            'protocol': 'ipv64',
            'auth_method': 'token',
            'token': 'your_update_token'
        }
        
        provider = create_provider(ipv64_config)
        self.assertIsInstance(provider, IPV64Provider)
        self.assertEqual(provider.name, 'my-ipv64')
        
        # Exact DynDNS2 config from example
        dyndns2_config = {
            'name': 'my-dyndns2',
            'protocol': 'dyndns2',
            'url': 'https://updates.dnsdynamic.org/api/',
            'auth_method': 'basic',
            'username': 'youruser',
            'password': 'yourpass',
            'hostname': 'yourdomain.dynu.net'
        }
        
        provider = create_provider(dyndns2_config)
        self.assertIsInstance(provider, DynDNS2Provider)
        self.assertEqual(provider.name, 'my-dyndns2')
    
    def test_case_insensitive_protocol_names(self):
        """Test that provider types are case-insensitive."""
        
        configs = [
            {'protocol': 'CLOUDFLARE', 'name': 'test1', 'zone': 'example.com', 'api_token': 'token', 'record_name': 'sub.example.com'},
            {'protocol': 'Cloudflare', 'name': 'test2', 'zone': 'example.com', 'api_token': 'token', 'record_name': 'sub.example.com'},
            {'protocol': 'cloudflare', 'name': 'test3', 'zone': 'example.com', 'api_token': 'token', 'record_name': 'sub.example.com'},
            {'protocol': 'IPV64', 'name': 'test4', 'token': 'token'},
        ]
        
        for config in configs:
            provider = create_provider(config)
            if 'cloudflare' in config['protocol'].lower():
                self.assertIsInstance(provider, CloudflareProvider)
            elif 'ipv64' in config['protocol'].lower():
                self.assertIsInstance(provider, IPV64Provider)

class TestProviderValidation(unittest.TestCase):
    """Test provider configuration validation."""
    
    def test_cloudflare_validation_real_fields(self):
        """Test Cloudflare validation with real config field names."""
        
        # Valid config
        valid_config = {
            'protocol': 'cloudflare',
            'name': 'test-cf',
            'zone': 'example.com',
            'api_token': 'test_token',
            'record_name': 'sub.example.com'
        }
        
        provider = create_provider(valid_config)
        # No exception should be raised during creation
        self.assertIsInstance(provider, CloudflareProvider)
        
        # Missing api_token
        invalid_config = {
            'protocol': 'cloudflare',
            'name': 'test-cf',
            'zone': 'example.com',
            'record_name': 'sub.example.com'
            # api_token missing
        }
        
        with self.assertRaises(ValueError):
            create_provider(invalid_config)
    
    def test_ipv64_validation_real_fields(self):
        """Test IPV64 validation with real config field names."""
        
        # Valid config with domain
        valid_config = {
            'protocol': 'ipv64',
            'name': 'test-ipv64',
            'token': 'test_token',
            'domain': 'example.com'
        }
        
        provider = create_provider(valid_config)
        self.assertIsInstance(provider, IPV64Provider)
        
        # Missing token
        invalid_config = {
            'protocol': 'ipv64',
            'name': 'test-ipv64',
            'domain': 'example.com'
            # token missing
        }
        
        with self.assertRaises(ValueError):
            create_provider(invalid_config)

if __name__ == '__main__':
    print("Running Provider Integration Tests...")
    print("=" * 50)
    unittest.main(verbosity=2)
