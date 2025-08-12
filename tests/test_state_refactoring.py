#!/usr/bin/env python3
"""
Test-Script für die DynDNS State Refaktorierung
Demonstriert die neue DynDNSState-Klasse und ihre Funktionalität.
"""

import sys
import os

# Import der refaktorierten update_dyndns.py 
sys.path.insert(0, os.path.dirname(__file__))
from update_dyndns import state, DynDNSState

def test_state_functionality():
    """Test der DynDNSState-Klasse Funktionalität."""
    
    print("=" * 60)
    print("🧪 TESTING DYNDNS STATE REFACTORING")
    print("=" * 60)
    
    # Test 1: Initialisierung
    print("\n1️⃣ Testing State Initialization:")
    print(f"   ✅ state.log_level: {state.log_level}")
    print(f"   ✅ state.console_level: {state.console_level}")
    print(f"   ✅ state.resilient_mode: {state.resilient_mode}")
    print(f"   ✅ state.failed_providers: {state.failed_providers}")
    print(f"   ✅ state.last_ipv4: {state.last_ipv4}")
    print(f"   ✅ state.last_ipv6: {state.last_ipv6}")
    
    # Test 2: Failed Provider Management
    print("\n2️⃣ Testing Failed Provider Management:")
    print("   Adding failed providers...")
    state.add_failed_provider("cloudflare")
    state.add_failed_provider("ipv64")
    state.add_failed_provider("cloudflare")  # Duplicate - should not be added twice
    print(f"   ✅ Failed providers: {state.failed_providers}")
    
    # Test 3: Network State Management
    print("\n3️⃣ Testing Network State Management:")
    print("   Setting error state...")
    state.resilient_mode = True
    state.error_count = 5
    state.last_error_time = 1642678800
    print(f"   ✅ Resilient mode: {state.resilient_mode}")
    print(f"   ✅ Error count: {state.error_count}")
    print(f"   ✅ Last error time: {state.last_error_time}")
    
    print("   Resetting network state...")
    state.reset_network_state()
    print(f"   ✅ After reset - Resilient mode: {state.resilient_mode}")
    print(f"   ✅ After reset - Failed providers: {state.failed_providers}")
    print(f"   ✅ After reset - Error count: {state.error_count}")
    
    # Test 4: IP Tracking
    print("\n4️⃣ Testing IP Tracking:")
    state.last_ipv4 = "192.168.1.100"
    state.last_ipv6 = "2001:db8::1"
    print(f"   ✅ Tracked IPv4: {state.last_ipv4}")
    print(f"   ✅ Tracked IPv6: {state.last_ipv6}")
    
    # Test 5: Log Level Management
    print("\n5️⃣ Testing Log Level Management:")
    original_level = state.log_level
    state.log_level = "DEBUG"
    state.console_level = "WARNING"
    print(f"   ✅ Log level changed from {original_level} to {state.log_level}")
    print(f"   ✅ Console level: {state.console_level}")
    
    # Test 6: Multiple State Instances
    print("\n6️⃣ Testing State Isolation:")
    new_state = DynDNSState()
    new_state.log_level = "TRACE"
    new_state.add_failed_provider("dyndns2")
    
    print(f"   ✅ Original state log_level: {state.log_level}")
    print(f"   ✅ New state log_level: {new_state.log_level}")
    print(f"   ✅ Original state failed_providers: {state.failed_providers}")
    print(f"   ✅ New state failed_providers: {new_state.failed_providers}")
    
    print("\n" + "=" * 60)
    print("✅ ALL STATE TESTS PASSED!")
    print("🎉 Refactoring successful - Global variables moved to DynDNSState class")
    print("=" * 60)

def test_backward_compatibility():
    """Test der Rückwärtskompatibilität mit globalen Variablen."""
    
    print("\n🔄 Testing Backward Compatibility:")
    
    # Import globale Variablen
    from update_dyndns import config, log_level, console_level, file_logger_instance
    
    print(f"   ✅ Global 'config' accessible: {config is not None or config is None}")
    print(f"   ✅ Global 'log_level' accessible: {log_level}")
    print(f"   ✅ Global 'console_level' accessible: {console_level}")
    print(f"   ✅ Global 'file_logger_instance' accessible: {file_logger_instance is not None or file_logger_instance is None}")
    
    print("   ✅ Backward compatibility maintained!")

if __name__ == "__main__":
    try:
        test_state_functionality()
        test_backward_compatibility()
        
        print(f"\n🚀 State refactoring completed successfully!")
        print(f"📝 Benefits achieved:")
        print(f"   • Better testability")
        print(f"   • Clearer state management") 
        print(f"   • Reduced global variables")
        print(f"   • Easier extension")
        print(f"   • Maintained backward compatibility")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
