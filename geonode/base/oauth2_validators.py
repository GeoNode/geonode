from oauth2_provider.oauth2_validators import OAuth2Validator


def get_user_groups_and_roles(user):
    group_names = list(user.groups.values_list("name", flat=True))
    roles = [f"ROLE_{name.upper()}" for name in group_names]
    if user.is_superuser:
        group_names.append("admin")
        roles.append("ROLE_ADMINISTRATOR")
    return group_names, roles


class GeoNodeOAuth2Validator(OAuth2Validator):

    def get_userinfo_claims(self, request):
        claims = super().get_userinfo_claims(request)
        user = request.user
        if user and not user.is_anonymous:
            claims["preferred_username"] = user.username
            claims["groups"], claims["roles"] = get_user_groups_and_roles(user)
        return claims
