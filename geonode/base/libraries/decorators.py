from django.http import Http404
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test
from geonode import settings


def superuser_check(user):
    if not user.is_superuser:
        raise Http404
    return user.is_superuser

def manager_or_member(user):
    if user.is_manager_of_any_group:
        return user.is_manager_of_any_group
    elif user.is_member_of_any_group:
        return user.is_member_of_any_group
    else:
        raise Http404

def organization_admin_required(view_func, redirect_field_name=REDIRECT_FIELD_NAME, login_url=settings.LOGIN_URL):
    """
    Decorator for views that checks that the user is logged in and is a staff
    member, displaying the login page if necessary.
    """
    return user_passes_test(
        lambda u: u.is_active and u.is_superuser or u.is_manager_of_any_group(),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )(view_func)