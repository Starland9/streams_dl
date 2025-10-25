"""
Global cache management for video download links.

This module provides caching functionality for video link retrieval operations
but does NOT cache search operations, as per requirements.
"""

import hashlib
import time
from typing import Any, Callable, Dict, List, Optional
from functools import wraps


class VideoCache:
    """
    Global cache for video download links.
    
    This cache stores the results of get_uqvideos_from_media_url calls
    to avoid repeatedly scraping the same URLs.
    """
    
    def __init__(self, ttl: int = 3600):
        """
        Initialize the video cache.
        
        Args:
            ttl: Time to live for cache entries in seconds (default: 1 hour)
        """
        self._cache: Dict[str, tuple[Any, float]] = {}
        self._ttl = ttl
    
    def _make_key(self, url: str, provider_name: str) -> str:
        """
        Generate a cache key from URL and provider name.
        
        Args:
            url: The media URL
            provider_name: The provider name
            
        Returns:
            A unique cache key
        """
        key_str = f"{provider_name}:{url}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, url: str, provider_name: str) -> Optional[List]:
        """
        Get cached video list if available and not expired.
        
        Args:
            url: The media URL
            provider_name: The provider name
            
        Returns:
            Cached video list or None if not found/expired
        """
        key = self._make_key(url, provider_name)
        
        if key in self._cache:
            value, timestamp = self._cache[key]
            
            # Check if cache entry has expired
            if time.time() - timestamp < self._ttl:
                return value
            else:
                # Remove expired entry
                del self._cache[key]
        
        return None
    
    def set(self, url: str, provider_name: str, value: List) -> None:
        """
        Store video list in cache.
        
        Args:
            url: The media URL
            provider_name: The provider name
            value: The video list to cache
        """
        key = self._make_key(url, provider_name)
        self._cache[key] = (value, time.time())
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
    
    def remove_expired(self) -> int:
        """
        Remove all expired cache entries.
        
        Returns:
            Number of entries removed
        """
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self._cache.items()
            if current_time - timestamp >= self._ttl
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        return len(expired_keys)


# Global cache instance
_global_cache = VideoCache()


def get_cache() -> VideoCache:
    """Get the global cache instance."""
    return _global_cache


def cache_video_links(func: Callable):
    """
    Decorator to cache the results of get_uqvideos_from_media_url methods.
    
    This decorator only works with async methods that have 'url' parameter
    and belong to a class with provider identification.
    """
    @wraps(func)
    async def wrapper(self, url: str, *args, **kwargs):
        # Get provider name from the class
        provider_name = self.__class__.__name__
        
        # Try to get from cache
        cache = get_cache()
        cached_result = cache.get(url, provider_name)
        
        if cached_result is not None:
            return cached_result
        
        # Call the original function
        result = await func(self, url, *args, **kwargs)
        
        # Store in cache
        cache.set(url, provider_name, result)
        
        return result
    
    return wrapper
