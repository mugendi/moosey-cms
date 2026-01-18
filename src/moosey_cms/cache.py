"""
Copyright (c) 2026 Anthony Mugendi
This software is released under the MIT License.
"""

from cachetools import TTLCache, cached
from cachetools.keys import hashkey
from functools import wraps

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

def cache_fn(cache=cache, debug=True):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 1. Convert Args/Kwargs to Hashable types
            # We don't change the actual args passed to the function,
            # we only change what we use to generate the lookup key.
            safe_args = tuple(make_hashable(a) for a in args)
            safe_kwargs = {k: make_hashable(v) for k, v in kwargs.items()}

            # 2. Generate Key using the safe versions
            key = hashkey(*safe_args, **safe_kwargs)

            # 3. Check Cache
            if key in cache:
                if debug:
                    print(' '*4, f'> Cache Hit For: "{func.__name__}"')
                return cache[key]

            # 4. Run Function (Using original args)
            result = func(*args, **kwargs)


            # 5. Store in Cache
            cache[key] = result
            return result

        return wrapper

    return decorator