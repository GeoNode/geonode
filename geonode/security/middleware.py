from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from re import compile
from guardian.shortcuts import get_anonymous_user


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
        reverse('layer_acls_dep'),
        reverse('layer_resolve_user'),
        reverse('layer_resolve_user_dep'),
        reverse('datarequests:data_request_form'),
        reverse('datarequests:profile_request_form'),
        reverse('datarequests:email_verification_send'),
        reverse('datarequests:email_verification_confirm')
        '/account/(?!.*(?:signup))',
        # block unauthenticated users from creating new accounts.
        '/static/*',
    )

    white_list = map(
        compile,
        white_list_paths +
        getattr(
            settings,
            "AUTH_EXEMPT_URLS",
            ()))
    redirect_to = reverse('account_login')

    def process_request(self, request):
        if not request.user.is_authenticated(
        ) or request.user == get_anonymous_user():
            if not any(path.match(request.path) for path in self.white_list):
                print('middleware security')
                return HttpResponseRedirect(
                    '{login_path}?next={request_path}'.format(
                        login_path=self.redirect_to,
                        request_path=request.path))
