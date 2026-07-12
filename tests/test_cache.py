import asyncio

import redis
import redis.asyncio

from moosey_cms.lib import cache as cache_module


class SyncRedis:
    def __init__(self):
        self.values = {}

    def get(self, key):
        return self.values.get(key)

    def set(self, key, value):
        self.values[key] = value

    def setex(self, key, _ttl, value):
        self.values[key] = value

    def delete(self, *keys):
        for key in keys:
            self.values.pop(key, None)

    def keys(self, pattern):
        prefix = pattern.removesuffix("*")
        return [key for key in self.values if key.startswith(prefix)]

    def scan_iter(self, match):
        yield from self.keys(match)


class AsyncRedis(SyncRedis):
    async def get(self, key):
        return self.values.get(key)

    async def set(self, key, value):
        self.values[key] = value

    async def setex(self, key, _ttl, value):
        self.values[key] = value

    async def delete(self, *keys):
        for key in keys:
            self.values.pop(key, None)

    async def keys(self, pattern):
        prefix = pattern.removesuffix("*")
        return [key for key in self.values if key.startswith(prefix)]


class WrappedAsyncRedis(AsyncRedis):
    """Mimics clients whose regular methods return coroutine objects."""

    def get(self, key):
        return super().get(key)


def configure_redis(monkeypatch):
    monkeypatch.setattr(cache_module.config.cache, "backend", "redis")
    monkeypatch.setattr(cache_module.config.cache, "redis_url", "redis://cache-test")


def test_cache_uses_sync_redis_client_for_sync_function(monkeypatch):
    configure_redis(monkeypatch)
    client = SyncRedis()
    monkeypatch.setattr(redis, "from_url", lambda _url: client)
    calls = 0

    @cache_module.cache()
    def cached_value(value):
        nonlocal calls
        calls += 1
        return value * 2

    assert cached_value(3) == 6
    assert cached_value(3) == 6
    assert calls == 1
    assert cached_value.cache_store.client is client


def test_cache_uses_async_redis_client_for_async_function(monkeypatch):
    configure_redis(monkeypatch)
    client = AsyncRedis()
    monkeypatch.setattr(redis.asyncio, "from_url", lambda _url: client)
    calls = 0

    @cache_module.cache()
    async def cached_value(value):
        nonlocal calls
        calls += 1
        return value * 2

    async def run():
        assert await cached_value(3) == 6
        assert await cached_value(3) == 6

    asyncio.run(run())
    assert calls == 1
    assert cached_value.cache_store.client is client


def test_async_store_adapts_sync_redis_client():
    client = SyncRedis()
    store = cache_module.RedisStore(client)

    async def run():
        await store.aset("answer", 42)
        assert await store.aget("answer") == 42
        await store.adelete("answer")
        assert await store.aget("answer") is None

    asyncio.run(run())


def test_async_store_awaits_result_from_wrapped_client_method():
    client = WrappedAsyncRedis()
    store = cache_module.RedisStore(client, is_async=True)

    async def run():
        await store.aset("answer", 42)
        assert await store.aget("answer") == 42

    asyncio.run(run())


def test_clear_cache_invalidates_registered_redis_namespace(monkeypatch):
    configure_redis(monkeypatch)
    client = SyncRedis()
    monkeypatch.setattr(redis, "from_url", lambda _url: client)
    calls = 0

    @cache_module.cache(key_prefix="invalidation-test:")
    def cached_value():
        nonlocal calls
        calls += 1
        return calls

    assert cached_value() == 1
    assert cached_value() == 1

    cache_module.clear_cache()

    assert not any(key.startswith("invalidation-test:") for key in client.values)
    assert cached_value() == 2


def test_file_changes_are_never_suppressed(monkeypatch):
    clears = 0

    def record_clear():
        nonlocal clears
        clears += 1

    monkeypatch.setattr(cache_module, "clear_cache", record_clear)
    cache_module.clear_cache_on_file_change("page.md", "modified")
    cache_module.clear_cache_on_file_change("page.md", "modified")

    assert clears == 2
