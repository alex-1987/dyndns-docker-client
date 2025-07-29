#!/usr/bin/env python3
"""
Simple test to verify provider creation fix
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from update_dyndns import create_provider

def test_provider_creation():
    """Test if provider creation works with real config formats."""
    
    print("Testing provider creation with real config formats...")
    print("=" * 50)
    
    # Test Cloudflare config (like in config.example.yaml)
    cloudflare_config = {
        'name': 'my-cloudflare',
        'protocol': 'cloudflare',
        'zone': 'example.com',
        'api_token': 'test_token',
        'record_name': 'sub.example.com'
    }
    
    try:
        provider = create_provider(cloudflare_config)
        print(f"✓ Cloudflare provider created successfully: {type(provider).__name__}")
    except Exception as e:
        print(f"✗ Cloudflare provider creation failed: {e}")
    
    # Test IPV64 config (like in config.example.yaml)
    ipv64_config = {
        'name': 'my-ipv64',
        'protocol': 'ipv64',
        'auth_method': 'token',
        'token': 'test_token'
    }
    
    try:
        provider = create_provider(ipv64_config)
        print(f"✓ IPV64 provider created successfully: {type(provider).__name__}")
    except Exception as e:
        print(f"✗ IPV64 provider creation failed: {e}")
    
    # Test DynDNS2 config (like in config.example.yaml)
    dyndns2_config = {
        'name': 'my-dyndns2',
        'protocol': 'dyndns2',
        'url': 'https://updates.dnsdynamic.org/api/',
        'auth_method': 'basic',
        'username': 'test_user',
        'password': 'test_pass',
        'hostname': 'test.example.com'
    }
    
    try:
        provider = create_provider(dyndns2_config)
        print(f"✓ DynDNS2 provider created successfully: {type(provider).__name__}")
    except Exception as e:
        print(f"✗ DynDNS2 provider creation failed: {e}")
    
    # Test unknown protocol
    unknown_config = {
        'name': 'unknown',
        'protocol': 'unknown_provider'
    }
    
    try:
        provider = create_provider(unknown_config)
        print(f"✗ Unknown provider should have failed but didn't")
    except ValueError as e:
        print(f"✓ Unknown provider properly rejected: {e}")
    except Exception as e:
        print(f"✗ Unknown provider failed with unexpected error: {e}")
    
    # Test missing protocol
    missing_protocol_config = {
        'name': 'missing-protocol'
    }
    
    try:
        provider = create_provider(missing_protocol_config)
        print(f"✗ Missing protocol should have failed but didn't")
    except ValueError as e:
        print(f"✓ Missing protocol properly rejected: {e}")
    except Exception as e:
        print(f"✗ Missing protocol failed with unexpected error: {e}")
    
    print("\nProvider creation test completed!")

if __name__ == '__main__':
    test_provider_creation()
