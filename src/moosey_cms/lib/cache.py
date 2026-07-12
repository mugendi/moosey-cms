"""
 Copyright (c) 2026 Anthony Mugendi
 
 This software is released under the MIT License.
 https://opensource.org/licenses/MIT
"""

import hashlib
import asyncio
import functools
import inspect
import time
import pickle
from typing import Any
def _pickle_dumps(v: Any) -> bytes:
    return pickle.dumps(v)

def _pickle_loads(v: bytes) -> Any:
    return pickle.loads(v)


# ── global store tracking ─────────────────────────────────────────────────────

_local_stores = []
_redis_prefixes = set()


def _register_local_store(store):
    _local_stores.append(store)


def _register_redis_prefix(prefix):
    _redis_prefixes.add(prefix)


def _clear_redis_cache():
    if not _redis_prefixes or config.cache.backend != "redis":
        return

    import redis

    client = redis.from_url(config.cache.redis_url)
    try:
        for prefix in _redis_prefixes:
            batch = []
            for key in client.scan_iter(match=f"{prefix}*"):
                batch.append(key)
                if len(batch) >= 500:
                    client.delete(*batch)
                    batch.clear()
            if batch:
                client.delete(*batch)
    finally:
        close = getattr(client, "close", None)
        if close is not None:
            close()


def clear_cache():
    """Clear all local stores and registered Redis cache namespaces."""
    for store in _local_stores:
        store.clear()
    _clear_redis_cache()


def clear_cache_on_file_change(file_path, event_type):
    clear_cache()


# ── local store ───────────────────────────────────────────────────────────────

class LocalStore:
    def __init__(self, maxsize):
        self.store = {}
        self.order = []
        self.maxsize = maxsize
        _register_local_store(self)

    def get(self, key):
        return self.store.get(key)          # (value, ts) | None

    def set(self, key, value, ts):
        if key not in self.store:
            self.order.append(key)
        self.store[key] = (value, ts)
        if self.maxsize and len(self.store) > self.maxsize:
            oldest = self.order.pop(0)
            self.store.pop(oldest, None)

    def delete(self, key):
        self.store.pop(key, None)
        if key in self.order:
            self.order.remove(key)

    def clear(self):
        self.store.clear()
        self.order.clear()


# ── redis store ───────────────────────────────────────────────────────────────

class RedisStore:
    """
    Wraps a redis.Redis or redis.asyncio.Redis client.
    Pass serializer='json' (default, safe) or 'pickle' (supports any Python object).
    """
    def __init__(self, client, prefix="cache:", serializer="json", is_async=None):
        self.client = client
        self.prefix = prefix
        self._is_async = (
            inspect.iscoroutinefunction(getattr(client, "get"))
            if is_async is None
            else is_async
        )

        self._dumps, self._loads = _pickle_dumps, _pickle_loads

    def _full_key(self, key: str) -> str:
        return f"{self.prefix}{key}"

    async def _async_call(self, method, *args, **kwargs):
        if self._is_async:
            result = method(*args, **kwargs)
        else:
            result = await asyncio.to_thread(method, *args, **kwargs)

        # Some clients expose regular wrapper methods which return awaitables,
        # so coroutine-function inspection alone is not reliable.
        if inspect.isawaitable(result):
            result = await result
        return result

    # sync ──────────────────────────────────
    def get(self, key):
        raw = self.client.get(self._full_key(key))
        return self._loads(raw) if raw is not None else None

    def set(self, key, value, ttl_seconds=None):
        raw = self._dumps(value)
        fk = self._full_key(key)
        if ttl_seconds:
            self.client.set(fk, raw, ex=int(ttl_seconds))
        else:
            self.client.set(fk, raw)

    def delete(self, key):
        self.client.delete(self._full_key(key))

    def clear(self, pattern="*"):
        keys = self.client.keys(f"{self.prefix}{pattern}")
        if keys:
            self.client.delete(*keys)

    # async ─────────────────────────────────
    async def aget(self, key):
        raw = await self._async_call(self.client.get, self._full_key(key))
        return self._loads(raw) if raw is not None else None

    async def aset(self, key, value, ttl_seconds=None):
        raw = self._dumps(value)
        fk = self._full_key(key)
        if ttl_seconds:
            await self._async_call(self.client.set, fk, raw, ex=int(ttl_seconds))
        else:
            await self._async_call(self.client.set, fk, raw)

    async def adelete(self, key):
        await self._async_call(self.client.delete, self._full_key(key))

    async def aclear(self, pattern="*"):
        keys = await self._async_call(self.client.keys, f"{self.prefix}{pattern}")
        if keys:
            await self._async_call(self.client.delete, *keys)


# ── decorator ─────────────────────────────────────────────────────────────────
from .config import load_config
config = load_config()

# print(config.cache.ttl)

def cache(maxsize=1000, ttl=config.cache.ttl, key_prefix="moosey-cache:"):
    """
    Args:
        maxsize:    local LRU limit (ignored when redis is set).
        ttl:        seconds until expiry (None = forever).
        key_prefix: redis key prefix, e.g. "myapp:users:".
    """

    use_redis = config.cache.backend == 'redis'



    local = None if use_redis else LocalStore(maxsize)

    if use_redis and not config.cache.redis_url:
        raise ValueError("cache.redis_url is required when the Redis backend is enabled")

    def make_key(func, args, kwargs):

        raw = f"{func.__module__}.{func.__qualname__}:{args}:{sorted(kwargs.items())}"
        return hashlib.sha256(raw.encode()).hexdigest()


    # ── decorator ─────────────────────────────────────────────────────────────
    def decorator(func):
        is_async = asyncio.iscoroutinefunction(func)

        if use_redis:
            _register_redis_prefix(key_prefix)
            if is_async:
                from redis import asyncio as redis_lib
            else:
                import redis as redis_lib
            client = redis_lib.from_url(config.cache.redis_url)
            redis_store = RedisStore(client, prefix=key_prefix, is_async=is_async)
        else:
            redis_store = None

        def sync_get(key):
            if redis_store is not None:
                entry = redis_store.get(key)
            else:
                entry = local.get(key)
            if entry is None:
                return None, False
            value, ts = entry
            if ttl is None or (time.monotonic() - ts) < ttl:
                return value, True
            if redis_store is not None:
                redis_store.delete(key)
            else:
                local.delete(key)
            return None, False

        def sync_set(key, value):
            ts = time.monotonic()
            if redis_store is not None:
                redis_store.set(key, (value, ts), ttl_seconds=ttl)
            else:
                local.set(key, value, ts)

        async def async_get(key):
            if redis_store is not None:
                entry = await redis_store.aget(key)
            else:
                entry = local.get(key)
            if entry is None:
                return None, False
            value, ts = entry
            if ttl is None or (time.monotonic() - ts) < ttl:
                return value, True
            if redis_store is not None:
                await redis_store.adelete(key)
            else:
                local.delete(key)
            return None, False

        async def async_set(key, value):
            ts = time.monotonic()
            if redis_store is not None:
                await redis_store.aset(key, (value, ts), ttl_seconds=ttl)
            else:
                local.set(key, value, ts)

        if is_async:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                key = make_key(func, args, kwargs)
                value, hit = await async_get(key)
                if hit:
                    return value
                value = await func(*args, **kwargs)
                await async_set(key, value)
                return value
        else:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                key = make_key(func, args, kwargs)
                value, hit = sync_get(key)
                if hit:
                    return value
                value = func(*args, **kwargs)
                sync_set(key, value)
                return value

        def cache_clear():
            if use_redis:
                raise RuntimeError("Call redis.clear() or redis.aclear() directly for async Redis.")
            else:
                local.clear()

        wrapper.cache_clear = cache_clear
        wrapper.cache_store = redis_store if use_redis else local
        return wrapper

    return decorator
