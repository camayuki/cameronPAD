"""
Caching layer for performance optimization.
"""
import json
import time
from typing import Any, Optional, Dict
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class CacheBackend(ABC):
    """Abstract cache backend."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """Clear all cache entries."""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass


class MemoryCacheBackend(CacheBackend):
    """In-memory cache backend."""
    
    def __init__(self, max_keys: int = 1000):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_keys = max_keys
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        
        # Check expiration
        if entry['expires_at'] and time.time() > entry['expires_at']:
            del self.cache[key]
            return None
        
        return entry['value']
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        # Evict old entries if at max capacity
        if len(self.cache) >= self.max_keys and key not in self.cache:
            self._evict_oldest()
        
        expires_at = None
        if ttl:
            expires_at = time.time() + ttl
        
        self.cache[key] = {
            'value': value,
            'expires_at': expires_at,
            'created_at': time.time()
        }
        
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    async def clear(self) -> bool:
        """Clear all cache entries."""
        self.cache.clear()
        return True
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if key not in self.cache:
            return False
        
        entry = self.cache[key]
        
        # Check expiration
        if entry['expires_at'] and time.time() > entry['expires_at']:
            del self.cache[key]
            return False
        
        return True
    
    def _evict_oldest(self) -> None:
        """Evict oldest cache entry."""
        if not self.cache:
            return
        
        oldest_key = min(
            self.cache.keys(),
            key=lambda k: self.cache[k]['created_at']
        )
        del self.cache[oldest_key]


class RedisCacheBackend(CacheBackend):
    """Redis cache backend."""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._redis = None
    
    async def _get_redis(self):
        """Get Redis connection."""
        if self._redis is None:
            import aioredis
            self._redis = aioredis.from_url(self.redis_url)
        return self._redis
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            redis = await self._get_redis()
            value = await redis.get(key)
            
            if value is None:
                return None
            
            # Deserialize value
            return json.loads(value.decode())
        
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        try:
            redis = await self._get_redis()
            
            # Serialize value
            serialized = json.dumps(value)
            
            if ttl:
                await redis.setex(key, ttl, serialized)
            else:
                await redis.set(key, serialized)
            
            return True
        
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            redis = await self._get_redis()
            result = await redis.delete(key)
            return result > 0
        
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    async def clear(self) -> bool:
        """Clear all cache entries."""
        try:
            redis = await self._get_redis()
            await redis.flushdb()
            return True
        
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            redis = await self._get_redis()
            result = await redis.exists(key)
            return result > 0
        
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False


class CacheManager:
    """Cache manager with multiple backends."""
    
    def __init__(self, backend: str = "memory", **kwargs):
        self.default_ttl = kwargs.get('default_ttl', 300)
        
        if backend == "memory":
            max_keys = kwargs.get('max_keys', 1000)
            self.backend = MemoryCacheBackend(max_keys)
        elif backend == "redis":
            redis_url = kwargs.get('redis_url')
            if not redis_url:
                raise ValueError("Redis URL is required for Redis backend")
            self.backend = RedisCacheBackend(redis_url)
        else:
            raise ValueError(f"Unsupported cache backend: {backend}")
        
        logger.info(f"Initialized cache with {backend} backend")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        return await self.backend.get(key)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        if ttl is None:
            ttl = self.default_ttl
        return await self.backend.set(key, value, ttl)
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        return await self.backend.delete(key)
    
    async def clear(self) -> bool:
        """Clear all cache entries."""
        return await self.backend.clear()
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        return await self.backend.exists(key)
    
    def cache_key(self, *parts) -> str:
        """Generate cache key from parts."""
        return ":".join(str(part) for part in parts)


class CacheDecorator:
    """Decorator for caching function results."""
    
    def __init__(self, cache_manager: CacheManager, ttl: Optional[int] = None, key_prefix: str = ""):
        self.cache_manager = cache_manager
        self.ttl = ttl
        self.key_prefix = key_prefix
    
    def __call__(self, func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = self._generate_key(func.__name__, args, kwargs)
            
            # Try to get from cache
            cached_result = await self.cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await self.cache_manager.set(cache_key, result, self.ttl)
            
            return result
        
        return wrapper
    
    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate cache key from function name and arguments."""
        key_parts = [self.key_prefix, func_name] if self.key_prefix else [func_name]
        
        # Add args to key
        for arg in args:
            if isinstance(arg, (str, int, float, bool)):
                key_parts.append(str(arg))
            else:
                # For complex objects, use their string representation
                key_parts.append(str(hash(str(arg))))
        
        # Add kwargs to key
        for k, v in sorted(kwargs.items()):
            if isinstance(v, (str, int, float, bool)):
                key_parts.append(f"{k}:{v}")
            else:
                key_parts.append(f"{k}:{hash(str(v))}")
        
        return self.cache_manager.cache_key(*key_parts)


# Global cache manager instance
_cache_manager = None


def get_cache_manager() -> CacheManager:
    """Get global cache manager."""
    global _cache_manager
    if _cache_manager is None:
        from .config import get_config
        config = get_config().cache
        
        _cache_manager = CacheManager(
            backend=config.backend,
            redis_url=config.redis_url,
            default_ttl=config.default_ttl,
            max_keys=config.max_keys
        )
    
    return _cache_manager


def cache(ttl: Optional[int] = None, key_prefix: str = ""):
    """Decorator for caching function results."""
    cache_manager = get_cache_manager()
    return CacheDecorator(cache_manager, ttl, key_prefix)