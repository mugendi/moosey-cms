"""
 Copyright (c) 2026 Anthony Mugendi
 
 This software is released under the MIT License.
 https://opensource.org/licenses/MIT
"""

import asyncio
import functools
import time
import json
import pickle
from typing import Any

# ── serializers ───────────────────────────────────────────────────────────────

def _json_dumps(v: Any) -> str:
    return json.dumps(v)

def _json_loads(v: str) -> Any:
    return json.loads(v)

def _pickle_dumps(v: Any) -> bytes:
    return pickle.dumps(v)

def _pickle_loads(v: bytes) -> Any:
    return pickle.loads(v)


# ── local store ───────────────────────────────────────────────────────────────

class LocalStore:
    def __init__(self, maxsize):
        self.store = {}
        self.order = []
        self.maxsize = maxsize

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
    def __init__(self, client, prefix="cache:", serializer="json"):
        self.client = client
        self.prefix = prefix
        self._is_async = asyncio.iscoroutinefunction(getattr(client, "get"))

        if serializer == "pickle":
            self._dumps, self._loads = _pickle_dumps, _pickle_loads
        else:
            self._dumps, self._loads = _json_dumps, _json_loads

    def _full_key(self, key: str) -> str:
        return f"{self.prefix}{key}"

    # sync ──────────────────────────────────
    def get(self, key):
        raw = self.client.get(self._full_key(key))
        return self._loads(raw) if raw is not None else None

    def set(self, key, value, ttl_seconds=None):
        raw = self._dumps(value)
        fk = self._full_key(key)
        if ttl_seconds:
            self.client.setex(fk, int(ttl_seconds), raw)
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
        raw = await self.client.get(self._full_key(key))
        return self._loads(raw) if raw is not None else None

    async def aset(self, key, value, ttl_seconds=None):
        raw = self._dumps(value)
        fk = self._full_key(key)
        if ttl_seconds:
            await self.client.setex(fk, int(ttl_seconds), raw)
        else:
            await self.client.set(fk, raw)

    async def adelete(self, key):
        await self.client.delete(self._full_key(key))

    async def aclear(self, pattern="*"):
        keys = await self.client.keys(f"{self.prefix}{pattern}")
        if keys:
            await self.client.delete(*keys)


# ── decorator ─────────────────────────────────────────────────────────────────

def cache(maxsize=128, ttl=None, redis=None, key_prefix="cache:"):
    """
    Args:
        maxsize:    local LRU limit (ignored when redis is set).
        ttl:        seconds until expiry (None = forever).
        redis:      a RedisStore instance (or None for local-only).
        key_prefix: redis key prefix, e.g. "myapp:users:".
    """
    use_redis = redis is not None
    local = None if use_redis else LocalStore(maxsize)

    def make_key(func, args, kwargs):
        raw = f"{func.__module__}.{func.__qualname__}:{args}:{sorted(kwargs.items())}"
        return raw  # use hashlib.sha256(raw.encode()).hexdigest() for very long keys

    # ── sync path ─────────────────────────────────────────────────────────────
    def sync_get(key):
        if use_redis:
            entry = redis.get(key)
            if entry is None:
                return None, False
            if ttl is None:
                return entry, True
            value, ts = entry
            if (time.monotonic() - ts) < ttl:
                return value, True
            redis.delete(key)
            return None, False
        else:
            entry = local.get(key)
            if entry is None:
                return None, False
            value, ts = entry
            if ttl is None or (time.monotonic() - ts) < ttl:
                return value, True
            local.delete(key)
            return None, False

    def sync_set(key, value):
        ts = time.monotonic()
        if use_redis:
            redis.set(key, (value, ts), ttl_seconds=ttl)
        else:
            local.set(key, value, ts)

    # ── async path ────────────────────────────────────────────────────────────
    async def async_get(key):
        if use_redis:
            entry = await redis.aget(key)
            if entry is None:
                return None, False
            if ttl is None:
                return entry, True
            value, ts = entry
            if (time.monotonic() - ts) < ttl:
                return value, True
            await redis.adelete(key)
            return None, False
        else:
            entry = local.get(key)
            if entry is None:
                return None, False
            value, ts = entry
            if ttl is None or (time.monotonic() - ts) < ttl:
                return value, True
            local.delete(key)
            return None, False

    async def async_set(key, value):
        ts = time.monotonic()
        if use_redis:
            await redis.aset(key, (value, ts), ttl_seconds=ttl)
        else:
            local.set(key, value, ts)

    # ── decorator ─────────────────────────────────────────────────────────────
    def decorator(func):
        is_async = asyncio.iscoroutinefunction(func)

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
        wrapper.cache_store = redis if use_redis else local
        return wrapper

    return decorator