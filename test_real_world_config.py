#!/usr/bin/env python3
"""
Test to simulate real-world configuration and verify unified provider architecture
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from update_dyndns import create_provider, update_provider

def test_real_world_config():
    """Test unified provider architecture with real-world configuration."""
    
    print("Testing unified provider architecture with real config...")
    print("=" * 60)
    
    # Simulate real configuration from config.example.yaml
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
            'token': 'ipv64_test_token_456'
        },
        {
            'name': 'my-dyndns2',
            'protocol': 'dyndns2',
            'url': 'https://updates.dnsdynamic.org/api/',
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
    print("\nTesting unified update_provider function...")
    print("-" * 40)
    
    for provider_config, provider_instance in created_providers:
        print(f"\nTesting {provider_config['name']}:")
        try:
            # This will try the unified architecture first, then fallback to legacy
            # We expect it to fallback since the providers delegate to legacy functions
            result = update_provider(provider_config, "192.168.1.100", None)
            print(f"  Result: {result}")
        except Exception as e:
            print(f"  Error: {e}")
    
    print("\n" + "=" * 60)
    print("Real-world configuration test completed!")

if __name__ == '__main__':
    test_real_world_config()
