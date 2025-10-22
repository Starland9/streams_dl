# Changelog



## [Unreleased] - 2025-01-XX

### Added
- **FlemmixProvider**: New streaming provider for Flemmix (formerly Wiflix) at https://flemmix.wiki/
  - Robust search implementation with multiple URL pattern fallbacks
  - Flexible episode extraction supporting both series and movies
  - Comprehensive video link extraction from multiple iframe and JavaScript sources
  - UQload link normalization for different URL formats
  - Multiple regex patterns for finding video links in various page structures
  
- **Multi-Provider Support**: API now supports multiple streaming providers
  - Added `provider_name` parameter to `/search` and `/get-videos` endpoints
  - New `/providers` endpoint to list available providers
  - Flemmix set as default provider
  - Support for provider selection via query/body parameters
  
- **Documentation**:
  - `README.md`: Comprehensive API documentation with examples
  - `IMPLEMENTATION.md`: Detailed implementation notes and architecture
  - `test_flemmix.py`: Test script for FlemmixProvider
  - `example_usage.py`: Example usage demonstration

### Changed
- **api.py**: Updated to support multiple providers with provider selection
  - Modified `/search` endpoint to accept optional `provider_name` parameter
  - Modified `/get-videos` endpoint to accept optional `provider_name` parameter
  - Updated API description to reflect multi-provider support
  - Changed default provider from PapaduStream to Flemmix

### Technical Details
- All providers now instantiated at startup and stored in a dictionary
- Provider validation added to prevent invalid provider names
- Error messages include list of available providers for user guidance

### Files Modified
- `api.py` (50 lines changed)

### Files Added
- `providers/flemmix.py` (429 lines)
- `README.md` (228 lines)
- `IMPLEMENTATION.md` (154 lines)
- `test_flemmix.py` (66 lines)
- `example_usage.py` (55 lines)
- `CHANGELOG.md` (this file)
