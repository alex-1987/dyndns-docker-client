#!/usr/bin/env python3
"""
Mock test to verify provider configuration compatibility without network calls
"""

import sys
import os
from unittest.mock import patch, MagicMock

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from update_dyndns import create_provider, update_provider

def test_provider_config_compatibility():
    """Test provider configuration compatibility with mock network calls."""
    
    print("Testing provider configuration compatibility (with mocks)...")
    print("=" * 60)
    
    # Mock all network functions to prevent actual API calls
    with patch('update_dyndns.requests.get') as mock_get, \
         patch('update_dyndns.requests.patch') as mock_patch, \
         patch('update_dyndns.get_cloudflare_zone_id') as mock_zone_id:
        
        # Setup mocks for successful responses
        mock_zone_id.return_value = "test_zone_id"
        
        # Mock Cloudflare responses
        mock_cloudflare_response = MagicMock()
        mock_cloudflare_response.json.return_value = {
            "success": True,
            "result": [{"id": "test_record_id", "content": "1.2.3.4"}]
        }
        mock_cloudflare_response.ok = True
        mock_get.return_value = mock_cloudflare_response
        mock_patch.return_value = mock_cloudflare_response
        
        # Mock IPV64 response
        mock_ipv64_response = MagicMock()
        mock_ipv64_response.text = "good 192.168.1.100"
        mock_ipv64_response.status_code = 200
        
        # Mock DynDNS2 response
        mock_dyndns2_response = MagicMock()
        mock_dyndns2_response.text = "good 192.168.1.100"
        
        # Use different responses for different URLs
        def mock_get_side_effect(url, **kwargs):
            if "cloudflare.com" in url:
                return mock_cloudflare_response
            elif "ipv64.net" in url:
                return mock_ipv64_response
            else:
                return mock_dyndns2_response
        
        mock_get.side_effect = mock_get_side_effect
        
        # Test configurations from config.example.yaml
        test_providers = [
            {
                'name': 'my-cloudflare',
                'protocol': 'cloudflare',
                'zone': 'example.com',
                'api_token': 'cf_test_token_123',
                'record_name': 'sub.example.com'
            },
            {   
                'name': 'my-ipv64',
                'protocol': 'ipv64',
                'auth_method': 'token',
                'token': 'ipv64_test_token_456',
                'domain': 'example.com'  # Add domain field that was missing
            },
            {
                'name': 'my-dyndns2',
                'protocol': 'dyndns2',
                'url': 'https://updates.example.com/api/',  # Use example.com to avoid DNS issues
                'auth_method': 'basic',
                'username': 'test_user',
                'password': 'test_pass',
                'hostname': 'test.example.com'
            }
        ]
        
        # Test provider creation for each
        created_providers = []
        for provider_config in test_providers:
            try:
                provider = create_provider(provider_config)
                print(f"✓ Created {provider_config['name']}: {type(provider).__name__}")
                created_providers.append((provider_config, provider))
            except Exception as e:
                print(f"✗ Failed to create {provider_config['name']}: {e}")
        
        print(f"\nSuccessfully created {len(created_providers)} providers")
        
        # Test the unified update_provider function
        print("\nTesting unified update_provider function (mocked)...")
        print("-" * 40)
        
        for provider_config, provider_instance in created_providers:
            print(f"\nTesting {provider_config['name']}:")
            try:
                # Test the unified architecture directly
                result = provider_instance.update_unified("192.168.1.100", None)
                print(f"  Unified result: {result}")
                
                # Test through main update_provider function
                result2 = update_provider(provider_config, "192.168.1.100", None)
                print(f"  Main function result: {result2}")
            except Exception as e:
                print(f"  Error: {e}")
    
    print("\n" + "=" * 60)
    print("Mock configuration test completed!")

def test_field_name_compatibility():
    """Test that providers handle different field name variations."""
    
    print("\n" + "=" * 60)
    print("Testing field name compatibility...")
    print("=" * 60)
    
    # Test Cloudflare with different token field names
    cloudflare_configs = [
        {
            'protocol': 'cloudflare',
            'name': 'cf-api-token',
            'zone': 'example.com',
            'api_token': 'test_token',  # Standard field name
            'record_name': 'sub.example.com'
        },
        {
            'protocol': 'cloudflare', 
            'name': 'cf-token',
            'zone': 'example.com',
            'token': 'test_token',  # Alternative field name
            'record_name': 'sub.example.com'
        }
    ]
    
    for config in cloudflare_configs:
        try:
            provider = create_provider(config)
            provider.validate_config()  # Test validation
            print(f"✓ Cloudflare config with '{list(config.keys())}' validated successfully")
        except Exception as e:
            print(f"✗ Cloudflare config failed: {e}")
    
    # Test IPV64 with different domain field names
    ipv64_configs = [
        {
            'protocol': 'ipv64',
            'name': 'ipv64-domain',
            'token': 'test_token',
            'domain': 'example.com'  # Standard field name
        },
        {
            'protocol': 'ipv64',
            'name': 'ipv64-host',
            'token': 'test_token',
            'host': 'example.com'  # Alternative field name
        },
        {
            'protocol': 'ipv64',
            'name': 'ipv64-hostname',
            'token': 'test_token',
            'hostname': 'example.com'  # Alternative field name
        }
    ]
    
    for config in ipv64_configs:
        try:
            provider = create_provider(config)
            provider.validate_config()  # Test validation
            domain_field = [k for k in ['domain', 'host', 'hostname'] if k in config][0]
            print(f"✓ IPV64 config with '{domain_field}' field validated successfully")
        except Exception as e:
            print(f"✗ IPV64 config failed: {e}")
    
    # Test DynDNS2 with different hostname field names
    dyndns2_configs = [
        {
            'protocol': 'dyndns2',
            'name': 'dyndns2-hostname',
            'url': 'https://example.com/api/',
            'hostname': 'example.com',  # Standard field name
            'auth_method': 'token',
            'token': 'test_token'
        },
        {
            'protocol': 'dyndns2',
            'name': 'dyndns2-domain',
            'url': 'https://example.com/api/',
            'domain': 'example.com',  # Alternative field name
            'auth_method': 'token',
            'token': 'test_token'
        },
        {
            'protocol': 'dyndns2',
            'name': 'dyndns2-host',
            'url': 'https://example.com/api/', 
            'host': 'example.com',  # Alternative field name
            'auth_method': 'basic',
            'username': 'user',
            'password': 'pass'
        }
    ]
    
    for config in dyndns2_configs:
        try:
            provider = create_provider(config)
            provider.validate_config()  # Test validation
            hostname_field = [k for k in ['hostname', 'domain', 'host'] if k in config][0]
            print(f"✓ DynDNS2 config with '{hostname_field}' field validated successfully")
        except Exception as e:
            print(f"✗ DynDNS2 config failed: {e}")
    
    print("\nField name compatibility test completed!")

if __name__ == '__main__':
    test_provider_config_compatibility()
    test_field_name_compatibility()
