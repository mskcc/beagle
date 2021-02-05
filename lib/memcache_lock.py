import time
import functools
from django.core.cache import cache

def memcache_lock(lock_id, expiration = 60 * 10):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            timeout_at = time.monotonic() + expiration - 3

            acquired = cache.add(lock_id, 1, expiration, noreply=False)
            if acquired:
                try:
                    func(self, *args, **kwargs)
                finally:
                    if time.monotonic() < timeout_at:
                        cache.delete(lock_id, noreply=False)
        return wrapper
    return decorator
