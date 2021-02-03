from allauth.socialaccount import providers
from django import template

register = template.Library()


@register.simple_tag
def get_user_social_providers(user):
    user_providers = set()
    for account in user.socialaccount_set.all():
        user_providers.add(account.get_provider())
    return list(user_providers)


@register.simple_tag
def get_other_social_providers(user):
    user_providers = get_user_social_providers(user)
    user_provider_names = [p.name.lower() for p in user_providers]
    other_providers = []
    for provider in providers.registry.get_list():
        if provider.name.lower() not in user_provider_names:
            other_providers.append(provider)
    return other_providers


@register.simple_tag
def get_number_unconnected_providers(user):
    return len(get_other_social_providers(user))


@register.simple_tag
def user_providers(user):
    return user.socialaccount_set.values_list("provider", flat=True)
