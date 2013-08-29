from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from re import compile

class LoginRequiredMiddleware(object):
    """
    Requires a user to be logged in to access any page that is not white-listed.
    """

    white_list_paths = (
        reverse('account_login'),
        reverse('forgot_username'),
        reverse('help'),
        reverse('jscat'),
        reverse('lang'),
        reverse('layer_acls'),
        reverse('layer_resolve_user'),
        '/account/(?!.*(?:signup))', # block unauthenticated users from creating new accounts.
        '/static/*',
    )

    white_list = map(compile, white_list_paths + getattr(settings, "AUTH_EXEMPT_URLS", ()))
    redirect_to = reverse('account_login')

    def process_request(self, request):
        if not request.user.is_authenticated() and not any(path.match(request.path) for path in self.white_list):
            return HttpResponseRedirect('{login_path}?next={request_path}'.format(login_path=self.redirect_to,
                                                                                  request_path=request.path))