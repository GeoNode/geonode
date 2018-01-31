from functools import wraps
from django.http import HttpResponse


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwrgs):
        from django.core.handlers.wsgi import WSGIRequest
        request = [a for a in args if isinstance(a, WSGIRequest)][0]
        user = request.__dict__.get('user', None) if request else None 
        if user is None or not user.is_authenticated():
            return HttpResponse(status=403)
        return fn(*args, **kwrgs)
    return wrapper