from guardian.shortcuts import get_anonymous_user

class AnonymousUserMiddleware(object):

    def process_request(self, request):
        if not request.user.is_authenticated():
            request.user = get_anonymous_user()