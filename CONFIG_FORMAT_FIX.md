# Configuration Format Compatibility Fix

## Problem

The user's configuration used `ip_services` (plural) format:
```yaml
ip_services:
  - "https://api.ipify.org"
  - "https://ifconfig.me/ip"
  - "https://icanhazip.com"
  # ...
```

But the code was only looking for `ip_service` (singular) in the main configuration parsing, causing the warning:
```
[WARNING] MAIN --> No method configured to determine IPv4
```

This triggered unnecessary resilient network mode activation.

## Solution

Updated the configuration parsing logic to support both formats:

### Key Changes in `update_dyndns.py`:

1. **Enhanced Configuration Parsing** (lines ~1025-1050):
   - Now checks for both `ip_service` and `ip_services`
   - If `ip_services` is provided but `ip_service` is not, uses the first service from the list
   - Similarly for IPv6 with `ip6_service` and `ip6_services`

2. **Improved Logging**:
   - Shows when multiple services are configured
   - Example: "Using primary service to determine IPv4: https://api.ipify.org (with 5 fallback services)"

3. **Enhanced Fallback Functions**:
   - `get_public_ip_with_fallback()` and `get_public_ipv6_with_fallback()` now handle both config formats
   - Respects user's service list while adding additional fallback services if needed

4. **Windows Compatibility Fix**:
   - Fixed fcntl import issue for Windows systems
   - Added conditional import and usage checks

## Supported Configuration Formats

### Singular Format (original):
```yaml
ip_service: "https://api.ipify.org"
ip6_service: "https://api64.ipify.org"
```

### Plural Format (new support):
```yaml
ip_services:
  - "https://api.ipify.org"
  - "https://ifconfig.me/ip"
  - "https://icanhazip.com"
ip6_services:
  - "https://api64.ipify.org"
  - "https://v6.ident.me"
```

### Mixed Format (also supported):
```yaml
ip_service: "https://api.ipify.org"  # Takes precedence
ip_services:
  - "https://ifconfig.me/ip"         # Additional fallback services
  - "https://icanhazip.com"
```

## Testing

Added comprehensive tests in `tests/test_basic_fixed.py`:
- `TestConfigurationFormats` class with 2 new tests
- Verifies both singular and plural formats work correctly
- Tests mixed configuration scenarios
- All 22 tests now pass (20 original + 2 new)

## Result

✅ User's configuration with `ip_services` (plural) now works correctly  
✅ No more "No method configured to determine IPv4" warning  
✅ Resilient mode only activates on actual network failures  
✅ Backward compatibility maintained for existing configs  
✅ Windows compatibility restored
