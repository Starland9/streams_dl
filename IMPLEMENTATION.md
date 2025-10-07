# FlemmixProvider Implementation Summary

## Overview

The FlemmixProvider is a new streaming provider implementation for the Flemmix (formerly Wiflix) streaming site at https://flemmix.wiki/. This provider follows the same architecture as existing providers (PapaduStreamProvider and FrenchStreamProvider).

## Key Features

### 1. **Robust Search Implementation**
- Tries multiple search URL patterns to handle site variations:
  - `/search/{query}`
  - `/recherche/{query}`
  - `/?s={query}`
- Uses multiple XPath patterns to find media items on different page structures
- Extracts title, URL, and image information from search results
- Limits results to 50 items maximum

### 2. **Flexible Episode Extraction**
- `_get_episode_links()` method tries multiple XPath patterns to find episodes
- Handles both series with multiple episodes and single movies
- Falls back to treating the page as a single video if no episodes are found

### 3. **Comprehensive Video Extraction**
- `_extract_uqload_from_page()` method:
  - Clicks play buttons to reveal video players
  - Extracts UQload links from iframes
  - Parses page source for embedded video links
  - Uses regex patterns to find different URL formats

### 4. **UQload Link Normalization**
- `_normalize_uqload_candidate()` method standardizes different UQload URL formats:
  - Embed URLs: `/embed-{code}.html`
  - File code parameters: `file_code={code}`
  - Various domain variants (uqload.cx, uqload.net)
  - Handles both direct and indirect link patterns

### 5. **Multiple Regex Patterns**
The provider uses several regex patterns to extract video links:
- `_UQLOAD_SOURCE_RE`: Finds video sources in JavaScript arrays
- `_UQLOAD_URL_RE`: Matches HTTP/HTTPS URLs
- `_UQLOAD_FILE_CODE_RE`: Extracts file codes from URLs
- `_UQLOAD_EMBED_RE`: Matches UQload embed URLs

## API Integration

### Multi-Provider Support

The API has been updated to support multiple providers:

1. **Provider Selection**: Users can specify which provider to use via `provider_name` parameter
2. **Default Provider**: Flemmix is set as the default provider
3. **Provider Discovery**: New `/providers` endpoint lists available providers

### API Endpoints Updated

1. **GET /providers**
   - Lists all available providers
   - Returns the default provider

2. **GET /search**
   - Added optional `provider_name` parameter
   - Default: "flemmix"
   - Validates provider exists before processing

3. **POST /get-videos**
   - Added optional `provider_name` parameter in request body
   - Default: "flemmix"
   - Uses the specified provider for video extraction

## Implementation Details

### Search Flow
```
search_media(query)
  ├─> Try multiple search URL patterns
  ├─> Find media items using multiple XPath patterns
  ├─> Extract title, URL, and image from each item
  └─> Return list of Media objects (max 50)
```

### Video Extraction Flow
```
get_uqvideos_from_media_url(url)
  ├─> _get_episode_links(url)
  │   ├─> Try multiple XPath patterns for episodes
  │   └─> Return episode URLs or [url] if none found
  ├─> For each episode:
  │   ├─> _extract_uqload_from_page(episode_url)
  │   │   ├─> Click play buttons
  │   │   ├─> Find iframes with uqload
  │   │   ├─> _collect_uqload_from_iframe()
  │   │   └─> _parse_uqload_links_from_html()
  │   └─> _normalize_uqload_candidate(link)
  └─> Return list of UqVideo objects
```

### Error Handling
- All methods use try-except blocks to handle failures gracefully
- Continues processing even if individual items fail
- Prints error messages for debugging
- Returns empty lists/sets on failures rather than crashing

### Performance Optimizations
- Uses `WebDriverWait` with configurable timeouts
- Implements cookie synchronization between Selenium and requests
- Caches user agent to avoid repeated queries
- Uses sets to deduplicate video links

## Code Quality

### Best Practices Followed
1. **Type Hints**: All methods have proper type annotations
2. **Documentation**: Comprehensive docstrings for public methods
3. **Constants**: Configuration values defined as class constants
4. **Separation of Concerns**: Each method has a single responsibility
5. **DRY Principle**: Reusable helper methods for common operations
6. **Error Resilience**: Graceful degradation on failures

### Patterns Used
- **Template Method**: Inherits from AbstractProvider
- **Strategy Pattern**: Different XPath strategies for different page layouts
- **Factory Pattern**: Creates Media and UqVideo objects
- **Session Management**: Proper setup and teardown of resources

## Testing

### Test Script (`test_flemmix.py`)
- Tests search functionality
- Tests episode extraction
- Provides detailed output for debugging
- Can be run with custom search queries

### Example Usage (`example_usage.py`)
- Demonstrates async usage
- Shows complete workflow from search to video extraction
- Serves as integration test

## Files Created/Modified

### New Files
1. `providers/flemmix.py` - Main provider implementation (429 lines)
2. `test_flemmix.py` - Test script (66 lines)
3. `example_usage.py` - Usage example
4. `README.md` - Complete documentation (228 lines)
5. `IMPLEMENTATION.md` - This file

### Modified Files
1. `api.py` - Updated to support multiple providers (50 lines changed)

## Deployment Notes

### Requirements
- Python 3.12+
- Selenium 4.26.1
- undetected-chromedriver
- FastAPI
- All other dependencies from requirements.txt

### Configuration
- Default provider can be changed in `api.py` by modifying `default_provider` variable
- Chrome options can be configured in the driver setup
- Timeouts can be adjusted via `DEFAULT_WAIT` constant

### Known Limitations
1. Requires the flemmix.wiki domain to be accessible
2. Site structure may change, requiring XPath updates
3. Depends on UQload video hosting
4. Chrome driver must be compatible with system Chrome version

## Future Enhancements

Potential improvements:
1. Add caching layer for search results
2. Implement retry logic with exponential backoff
3. Add more video hosting provider support beyond UQload
4. Implement parallel episode processing
5. Add progress callbacks for long operations
6. Support for subtitles/audio tracks extraction
7. Quality selection preferences
