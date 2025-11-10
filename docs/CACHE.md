# Cache Implementation for Video Download Links

## Overview

The application now includes a **global cache mechanism** for video download links retrieval. This cache significantly improves performance by avoiding redundant web scraping operations for the same media URLs.

## Key Features

### ✅ What IS Cached
- **Video link retrieval** via `get_uqvideos_from_media_url()` method
- Results are cached per provider and URL combination
- Default TTL (Time To Live): 1 hour (3600 seconds)

### ❌ What is NOT Cached
- **Search operations** via `search_media()` method
- This ensures users always get fresh search results

## Implementation Details

### Cache Module (`cache.py`)

The cache implementation provides:

1. **VideoCache Class**: A simple in-memory cache with TTL support
   - Stores video lists by URL and provider combination
   - Automatically expires entries after TTL
   - Thread-safe for concurrent operations

2. **Global Cache Instance**: A singleton cache shared across all providers
   - Accessible via `get_cache()`
   - Used by all three providers (Flemmix, FrenchStream, PapaduStream)

3. **Decorator**: `@cache_video_links`
   - Automatically caches results of `get_uqvideos_from_media_url()`
   - Transparent to callers - no code changes needed
   - Provider-specific caching (same URL in different providers cached separately)

### How It Works

```python
# Example flow:
# 1. First request to get videos
result = await provider.get_uqvideos_from_media_url("http://example.com/video")
# → Fetches from website, stores in cache

# 2. Second request to same URL (within TTL)
result = await provider.get_uqvideos_from_media_url("http://example.com/video")
# → Returns cached result instantly, no web scraping
```

## Performance Benefits

- **Reduced Load**: Fewer requests to streaming sites
- **Faster Response**: Cached results return instantly
- **Better User Experience**: Quicker API responses for repeated requests
- **Resource Efficient**: Less CPU and network usage

## Cache Key Format

Cache keys are generated using:
```
MD5("{provider_name}:{media_url}")
```

This ensures:
- Same URL in different providers are cached separately
- Efficient lookup with consistent key format
- No collisions between providers

## Provider Integration

All three providers now use the cache:

1. **FrenchStreamProvider**
   - `get_uqvideos_from_media_url()` decorated with `@cache_video_links`
   - `search_media()` NOT cached

2. **FlemmixProvider**
   - `get_uqvideos_from_media_url()` decorated with `@cache_video_links`
   - `search_media()` NOT cached

3. **PapaduStreamProvider**
   - `get_uqvideos_from_media_url()` decorated with `@cache_video_links`
   - `search_media()` NOT cached

## API Behavior

### `/search` Endpoint
- **Not cached** - Always performs fresh search
- Ensures users get latest content

### `/get-videos` Endpoint
- **Cached** - Returns cached results within TTL
- First request scrapes website and caches
- Subsequent requests return instantly from cache

## Configuration

The default TTL is 1 hour (3600 seconds). To modify:

```python
from cache import get_cache

# Change TTL for all future cache entries
cache = get_cache()
cache._ttl = 7200  # 2 hours
```

## Cache Management

### Clear Cache
```python
from cache import get_cache

cache = get_cache()
cache.clear()  # Removes all cached entries
```

### Remove Expired Entries
```python
from cache import get_cache

cache = get_cache()
count = cache.remove_expired()  # Returns number of entries removed
```

## Testing

The cache implementation includes comprehensive tests:
- Basic cache operations (get/set)
- TTL expiration
- Provider-specific caching
- Decorator functionality

Run tests:
```bash
cd /home/runner/work/streams_dl/streams_dl
PYTHONPATH=/home/runner/work/streams_dl/streams_dl python /tmp/test_cache.py
```

## Technical Details

### Storage
- **In-memory**: Cache stored in Python dictionary
- **Persistence**: Cache does NOT persist across app restarts
- **Scope**: Global across all provider instances

### Thread Safety
- Uses Python's GIL for basic thread safety
- Safe for concurrent FastAPI requests

### Memory Management
- Automatic expiration of old entries
- Manual cleanup available via `remove_expired()`
- Consider implementing max cache size for production

## Future Enhancements

Potential improvements:
- Redis/Memcached backend for distributed caching
- Configurable TTL per provider
- Cache size limits
- Cache statistics and monitoring
- Persistent cache storage

## Implementation Notes

This implementation fulfills the requirement:
> "rajoute la gestion globale cache lors de la récupération des liens de téléchargement des vidéos mais pas lors de la recherche"

Translation:
> "Add global cache management when retrieving video download links but not during search"

✅ Implemented as specified with minimal code changes
✅ All three providers updated
✅ Search operations remain uncached
✅ Video link retrieval is now cached globally
