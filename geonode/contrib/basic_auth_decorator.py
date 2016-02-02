from django.http import HttpResponse
from django.contrib.auth import authenticate, login
from functools import wraps
from geonode.contrib.dataverse_connect.dv_utils import MessageHelperJSON


def http_basic_auth_for_api(view_func):
    """
    Decorator for an API request, use HTTP basic authentication
    Based on Django snippets: https://djangosnippets.org/snippets/1304/ and  https://djangosnippets.org/snippets/2313/

    On failure, return a 401 and JSON message similar to:
        {"message": "Login Failed", "success": false}

    :param view_func:
    :return:
    """
    @wraps(view_func)
    def _decorator(request, *args, **kwargs):

        # (1) Does this request have HTTP_AUTHORIZATION?
        #
        if not 'HTTP_AUTHORIZATION' in request.META:
            # json_msg = json.dumps(dict(success=False, message="Login required"))
            json_msg = MessageHelperJSON.get_json_fail_msg("Login required")
            return HttpResponse(status=401, content=json_msg, content_type="application/json")

        # (2) Get username and password from the HTTP_AUTHORIZATION
        #       and try to login
        #
        authmeth, auth = request.META['HTTP_AUTHORIZATION'].split(' ', 1)
        if authmeth.lower() == 'basic':
            auth = auth.strip().decode('base64')
            username, password = auth.split(':', 1)
            # (2a) Attempt to authenticate
            #
            user = authenticate(username=username, password=password)
            if user is not None and user.is_active:
                # (2b) Authentication success, now log in
                #
                login(request, user)

                # (2c) return to the view logged in
                #
                return view_func(request, *args, **kwargs)

        # Nope, the log in Failed
        #
        json_msg = MessageHelperJSON.get_json_fail_msg("Login failed")
        #json_msg = json.dumps(dict(success=False, message="Login failed"))
        return HttpResponse(status=401, content=json_msg, content_type="application/json")

    return _decorator
