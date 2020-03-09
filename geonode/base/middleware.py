from django.shortcuts import render
from geonode.base.models import Configuration


class ReadOnlyMiddleware:
    """
    A Middleware disabling all content modifying requests, if read-only Configuration setting is True,
    with an exception for whitelisted url names.
    """

    FORBIDDEN_HTTP_METHODS = [
        'POST', 'PUT', 'DELETE'
    ]

    WHITELISTED_URL_NAMES = [
        'login',
        'logout',
        'account_login',
        'account_logout',
        'ows_endpoint',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):

        # check if the Geonode instance is read-only
        if Configuration.load().read_only:
            # allow superadmin users to do whatever they want
            if not request.user.is_superuser or not request.user.is_active:
                # check if the request's method is forbidden in read-only instance
                if request.method in self.FORBIDDEN_HTTP_METHODS:
                    # check if the request is not against whitelisted views (check by URL names)
                    if request.resolver_match.url_name not in self.WHITELISTED_URL_NAMES:
                        # return HttpResponse('Error: Instance in read-only mode', status=405)
                        return render(request, 'base/read_only_violation.html', status=405)


class MaintenanceMiddleware:
    """
    A Middleware redirecting all requests to maintenance info page, except:
        - admin panel login,
        - admin panel logout,
        - requests performed by superuser,
    if maintenance Configuration setting is True.
    """

    # URL's enabling superuser to login/logout to/from admin panel
    WHITELISTED_URL_NAMES = [
        'login',
        'logout',
        'index',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):

        # check if the Geonode instance is read-only
        if Configuration.load().maintenance:
            # allow superadmin users to do whatever they want
            if not request.user.is_superuser:
                # check if the request is not against whitelisted views (check by URL names)
                if request.resolver_match.url_name not in self.WHITELISTED_URL_NAMES:
                    return render(request, 'base/maintenance.html', status=503)
