"""
Intelligent caching system for Jarvis.
Provides multi-level caching with LRU eviction, TTL support, and smart invalidation.
"""
import time
import json
import hashlib
import threading
from typing import Any, Dict, Optional, List, Callable, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import logging

class CacheLevel(Enum):
    """Cache levels with different persistence."""
    MEMORY = "memory"
    DISK = "disk"
    DISTRIBUTED = "distributed"

@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    value: Any
    created_at: float
    last_accessed: float
    access_count: int
    ttl: Optional[float] = None
    size: int = 0
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.size == 0:
            self.size = len(str(self.value).encode('utf-8'))
    
    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.ttl is None:
            return False
        return time.time() > (self.created_at + self.ttl)
    
    def touch(self):
        """Update last access time and count."""
        self.last_accessed = time.time()
        self.access_count += 1

class CachePolicy:
    """Cache eviction policies."""
    
    @staticmethod
    def lru(entries: Dict[str, CacheEntry], max_size: int) -> List[str]:
        """Least Recently Used eviction."""
        return sorted(entries.keys(), key=lambda k: entries[k].last_accessed)[:max_size]
    
    @staticmethod
    def lfu(entries: Dict[str, CacheEntry], max_size: int) -> List[str]:
        """Least Frequently Used eviction."""
        return sorted(entries.keys(), key=lambda k: entries[k].access_count)[:max_size]
    
    @staticmethod
    def ttl(entries: Dict[str, CacheEntry], max_size: int) -> List[str]:
        """TTL-based eviction (remove expired first)."""
        expired = [k for k, v in entries.items() if v.is_expired()]
        if len(expired) >= max_size:
            return expired[:max_size]
        
        # If not enough expired, remove oldest
        remaining = max_size - len(expired)
        oldest = sorted([k for k in entries.keys() if k not in expired], 
                       key=lambda k: entries[k].created_at)[:remaining]
        return expired + oldest

class IntelligentCache:
    """Multi-level intelligent caching system."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger("Jarvis.Cache")
        
        # Cache configuration
        self.memory_limit = self.config.get("memory_limit", 100)  # Max entries
        self.disk_limit = self.config.get("disk_limit", 1000)
        self.default_ttl = self.config.get("default_ttl", 3600)  # 1 hour
        self.cleanup_interval = self.config.get("cleanup_interval", 300)  # 5 minutes
        self.cache_dir = Path(self.config.get("cache_dir", "cache"))
        self.cache_dir.mkdir(exist_ok=True)
        
        # Cache storage
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.disk_cache_file = self.cache_dir / "disk_cache.json"
        self.disk_cache: Dict[str, CacheEntry] = self._load_disk_cache()
        
        # Cache statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "memory_size": 0,
            "disk_size": 0
        }
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Start cleanup thread
        self._start_cleanup_thread()
        
        self.logger.info(f"Intelligent cache initialized: memory_limit={self.memory_limit}, disk_limit={self.disk_limit}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        with self.lock:
            # Try memory cache first
            if key in self.memory_cache:
                entry = self.memory_cache[key]
                if not entry.is_expired():
                    entry.touch()
                    self.stats["hits"] += 1
                    self.logger.debug(f"Cache hit (memory): {key}")
                    return entry.value
                else:
                    del self.memory_cache[key]
                    self.stats["evictions"] += 1
            
            # Try disk cache
            if key in self.disk_cache:
                entry = self.disk_cache[key]
                if not entry.is_expired():
                    entry.touch()
                    # Promote to memory cache
                    self._add_to_memory(key, entry.value, entry.ttl, entry.tags)
                    self.stats["hits"] += 1
                    self.logger.debug(f"Cache hit (disk): {key}")
                    return entry.value
                else:
                    del self.disk_cache[key]
                    self._save_disk_cache()
                    self.stats["evictions"] += 1
            
            self.stats["misses"] += 1
            self.logger.debug(f"Cache miss: {key}")
            return default
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None, tags: List[str] = None) -> bool:
        """Set value in cache."""
        with self.lock:
            ttl = ttl or self.default_ttl
            tags = tags or []
            
            # Add to memory cache
            success = self._add_to_memory(key, value, ttl, tags)
            
            # Also add to disk cache for persistence
            if success:
                self._add_to_disk(key, value, ttl, tags)
            
            return success
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        with self.lock:
            deleted = False
            
            if key in self.memory_cache:
                del self.memory_cache[key]
                deleted = True
            
            if key in self.disk_cache:
                del self.disk_cache[key]
                self._save_disk_cache()
                deleted = True
            
            return deleted
    
    def clear(self, pattern: str = None, tags: List[str] = None) -> int:
        """Clear cache entries by pattern or tags."""
        with self.lock:
            cleared = 0
            
            if pattern:
                import re
                regex = re.compile(pattern, re.IGNORECASE)
                
                # Clear from memory
                keys_to_remove = [k for k in self.memory_cache.keys() if regex.search(k)]
                for key in keys_to_remove:
                    del self.memory_cache[key]
                    cleared += 1
                
                # Clear from disk
                keys_to_remove = [k for k in self.disk_cache.keys() if regex.search(k)]
                for key in keys_to_remove:
                    del self.disk_cache[key]
                    cleared += 1
            
            elif tags:
                # Clear by tags
                for cache in [self.memory_cache, self.disk_cache]:
                    keys_to_remove = [k for k, v in cache.items() 
                                  if any(tag in v.tags for tag in tags)]
                    for key in keys_to_remove:
                        del cache[key]
                        cleared += 1
            
            else:
                # Clear all
                cleared = len(self.memory_cache) + len(self.disk_cache)
                self.memory_cache.clear()
                self.disk_cache.clear()
            
            if cleared > 0:
                self._save_disk_cache()
            
            return cleared
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            total_requests = self.stats["hits"] + self.stats["misses"]
            hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "hit_rate": round(hit_rate, 2),
                "total_requests": total_requests,
                "memory_entries": len(self.memory_cache),
                "disk_entries": len(self.disk_cache),
                "memory_size_bytes": sum(e.size for e in self.memory_cache.values()),
                "disk_size_bytes": sum(e.size for e in self.disk_cache.values()),
                "evictions": self.stats["evictions"],
                "cleanup_interval": self.cleanup_interval
            }
    
    def _add_to_memory(self, key: str, value: Any, ttl: Optional[float], tags: List[str]) -> bool:
        """Add entry to memory cache with eviction."""
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=time.time(),
            last_accessed=time.time(),
            access_count=1,
            ttl=ttl,
            tags=tags
        )
        
        # Check if we need to evict
        if len(self.memory_cache) >= self.memory_limit:
            evicted_keys = CachePolicy.lru(self.memory_cache, self.memory_limit // 4)
            for evicted_key in evicted_keys:
                del self.memory_cache[evicted_key]
                self.stats["evictions"] += 1
        
        self.memory_cache[key] = entry
        return True
    
    def _add_to_disk(self, key: str, value: Any, ttl: Optional[float], tags: List[str]) -> bool:
        """Add entry to disk cache."""
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=time.time(),
            last_accessed=time.time(),
            access_count=1,
            ttl=ttl,
            tags=tags
        )
        
        # Check if we need to evict
        if len(self.disk_cache) >= self.disk_limit:
            evicted_keys = CachePolicy.lfu(self.disk_cache, self.disk_limit // 4)
            for evicted_key in evicted_keys:
                del self.disk_cache[evicted_key]
                self.stats["evictions"] += 1
        
        self.disk_cache[key] = entry
        self._save_disk_cache()
        return True
    
    def _load_disk_cache(self) -> Dict[str, CacheEntry]:
        """Load disk cache from file."""
        if not self.disk_cache_file.exists():
            return {}
        
        try:
            with open(self.disk_cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            cache = {}
            for key, entry_data in data.items():
                # Filter expired entries
                entry = CacheEntry(**entry_data)
                if not entry.is_expired():
                    cache[key] = entry
            
            self.logger.info(f"Loaded {len(cache)} entries from disk cache")
            return cache
            
        except Exception as e:
            self.logger.error(f"Failed to load disk cache: {e}")
            return {}
    
    def _save_disk_cache(self):
        """Save disk cache to file."""
        try:
            # Convert to serializable format
            data = {}
            for key, entry in self.disk_cache.items():
                entry_data = asdict(entry)
                # Handle non-serializable values
                try:
                    json.dumps(entry_data["value"])
                except (TypeError, ValueError):
                    entry_data["value"] = str(entry_data["value"])
                data[key] = entry_data
            
            with open(self.disk_cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save disk cache: {e}")
    
    def _cleanup_expired(self):
        """Clean up expired entries."""
        with self.lock:
            # Clean memory cache
            expired_keys = [k for k, v in self.memory_cache.items() if v.is_expired()]
            for key in expired_keys:
                del self.memory_cache[key]
                self.stats["evictions"] += 1
            
            # Clean disk cache
            expired_keys = [k for k, v in self.disk_cache.items() if v.is_expired()]
            for key in expired_keys:
                del self.disk_cache[key]
                self.stats["evictions"] += 1
            
            if expired_keys:
                self._save_disk_cache()
                self.logger.debug(f"Cleaned up {len(expired_keys)} expired entries")
    
    def _start_cleanup_thread(self):
        """Start background cleanup thread."""
        def cleanup_worker():
            while True:
                time.sleep(self.cleanup_interval)
                self._cleanup_expired()
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
        self.logger.info("Cache cleanup thread started")

# Decorator for automatic caching
def cache_result(ttl: Optional[float] = None, tags: List[str] = None, key_func: Callable = None):
    """Decorator to cache function results."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = hashlib.md5("|".join(key_parts).encode()).hexdigest()
            
            # Get cache instance
            cache = get_cache_instance()
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl, tags)
            
            return result
        
        return wrapper
    return decorator

# Global cache instance
_cache_instance = None

def get_cache_instance() -> IntelligentCache:
    """Get global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = IntelligentCache()
    return _cache_instance

def configure_cache(config: Dict[str, Any]):
    """Configure global cache instance."""
    global _cache_instance
    _cache_instance = IntelligentCache(config)
