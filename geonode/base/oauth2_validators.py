from oauth2_provider.oauth2_validators import OAuth2Validator


class GeoNodeOAuth2Validator(OAuth2Validator):

    def get_userinfo_claims(self, request):
        claims = super().get_userinfo_claims(request)
        user = request.user
        if user and not user.is_anonymous:
            claims["preferred_username"] = user.username
            groups = [g.name for g in user.groups.all()]
            if user.is_superuser:
                groups.append("admin")
            claims["groups"] = groups
        return claims
