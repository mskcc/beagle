import time
import functools
from django.core.cache import cache
from contextlib import contextmanager


LOCK_EXPIRE = 60 * 10  # Lock expires in 10 minutes


def memcache_lock(lock_id, expiration=60 * 10):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            timeout_at = time.monotonic() + expiration - 3

            acquired = cache.add(lock_id, 1, expiration)
            if acquired:
                try:
                    func(*args, **kwargs)
                finally:
                    if time.monotonic() < timeout_at:
                        cache.delete(lock_id)

        return wrapper

    return decorator


@contextmanager
def memcache_task_lock(lock_id, oid):
    """
    https://docs.celeryproject.org/en/stable/tutorials/task-cookbook.html
    This method is used when you want to acquire lock on object:
    Example:
       orchestrator.tasks.command_processor
    :param lock_id:
    :param oid:
    :return:
    """
    timeout_at = time.monotonic() + LOCK_EXPIRE - 3
    # cache.add fails if the key already exists
    status = cache.add(lock_id, oid, LOCK_EXPIRE)
    try:
        yield status
    finally:
        # memcache delete is very slow, but we have to use it to take
        # advantage of using add() for atomic locking
        if time.monotonic() < timeout_at and status:
            # don't release the lock if we exceeded the timeout
            # to lessen the chance of releasing an expired lock
            # owned by someone else
            # also don't release the lock if we didn't acquire it
            cache.delete(lock_id)
