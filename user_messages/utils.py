try:
    from functools import wraps
except ImportError:
    from django.utils.functional import wraps  # Python 2.4 fallback.


def cached_attribute(func):
    cache_name = "_%s" % func.__name__
    @wraps(func)
    def inner(self, *args, **kwargs):
        if hasattr(self, cache_name):
            return getattr(self, cache_name)
        val = func(self, *args, **kwargs)
        setattr(self, cache_name, val)
        return val
    return inner
