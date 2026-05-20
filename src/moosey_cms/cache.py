"""
Copyright (c) 2026 Anthony Mugendi
This software is released under the MIT License.
"""

from cachetools import TTLCache, cached
from cachetools.keys import hashkey
from functools import wraps
import inspect

# Cache with TTL of 30 days
cache = TTLCache(maxsize=1000, ttl=3600 * 24 * 30)

def clear_cache():
    cache.clear()


# clear once even for multiple filess
@cached(TTLCache(maxsize=100, ttl=5))
def clear_cache_on_file_change(file_path, event_type):
    # print(f"File {file_path} changed.")
    clear_cache()

# --- HELPER: Convert mutable types to immutable (hashable) ---
def make_hashable(value):
    """
    Recursively converts dictionaries to sorted tuples of items,
    and lists to tuples. This allows them to be hashed for caching.
    """
    if isinstance(value, dict):
        return tuple(sorted((k, make_hashable(v)) for k, v in value.items()))
    elif isinstance(value, (list, set)):
        return tuple(make_hashable(v) for v in value)
    return value

def cache_fn(cache=cache, debug=False, exclude_args=None):
    """
    Works with BOTH sync and async functions.
    """

    if exclude_args is None:
        exclude_args = ['templates']

    def decorator(func):

        is_async = inspect.iscoroutinefunction(func)

        # =========================================================
        # ASYNC VERSION
        # =========================================================
        if is_async:

            @wraps(func)
            async def async_wrapper(*args, **kwargs):

                args_to_hash = tuple(
                    make_hashable(a)
                    for i, a in enumerate(args)
                    if i not in exclude_args
                )

                kwargs_to_hash = {
                    k: make_hashable(v)
                    for k, v in kwargs.items()
                    if k not in exclude_args
                }

                key = hashkey(*args_to_hash, **kwargs_to_hash)

                if key in cache:
                    if debug:
                        print(' ' * 4, f'> Async Cache Hit For: "{func.__name__}"')
                    return cache[key]

                result = await func(*args, **kwargs)

                cache[key] = result

                return result

            return async_wrapper

        # =========================================================
        # SYNC VERSION
        # =========================================================
        @wraps(func)
        def sync_wrapper(*args, **kwargs):

            args_to_hash = tuple(
                make_hashable(a)
                for i, a in enumerate(args)
                if i not in exclude_args
            )

            kwargs_to_hash = {
                k: make_hashable(v)
                for k, v in kwargs.items()
                if k not in exclude_args
            }

            key = hashkey(*args_to_hash, **kwargs_to_hash)

            if key in cache:
                if debug:
                    print(' ' * 4, f'> Cache Hit For: "{func.__name__}"')
                return cache[key]

            result = func(*args, **kwargs)

            cache[key] = result

            return result

        return sync_wrapper

    return decorator
    