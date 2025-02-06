#########################################################################
#
# Copyright (C) 2017 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

"""Custom account adapters for django-allauth.

These are used in order to extend the default authorization provided by
django-allauth.

"""

import logging
import re
import jwt
import requests

from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.utils import user_field
from allauth.account.utils import user_email
from allauth.account.utils import user_username
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.providers.oauth2.views import OAuth2Adapter, OAuth2Error

from invitations.adapters import BaseInvitationsAdapter

from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.core.exceptions import ValidationError
from django.utils.module_loading import import_string
from django.core.exceptions import ImproperlyConfigured
from geonode.groups.models import GroupProfile

logger = logging.getLogger(__name__)


def get_data_extractor(provider_id):
    """Get the relevant profile extractor instance for the provider

    Retrieve the data extractor instance to use for getting profile
    information from social account providers.

    """

    extractors = getattr(settings, "SOCIALACCOUNT_PROFILE_EXTRACTORS", {})
    extractor_path = extractors.get(provider_id)
    if extractor_path is not None:
        extractor_class = import_string(extractor_path)
        extractor = extractor_class()
    else:
        extractor = None
    return extractor


def get_group_role_mapper(provider_id):
    group_role_mapper_class = import_string(
        getattr(settings, "SOCIALACCOUNT_PROVIDERS", {})
        .get(PROVIDER_ID, {})
        .get(
            "GROUP_ROLE_MAPPER_CLASS",
            "geonode.people.profileextractors.OpenIDGroupRoleMapper",
        )
    )
    return group_role_mapper_class()


def update_profile(sociallogin):
    """Update a people.models.Profile object with info from the sociallogin"""
    user = sociallogin.user
    extractor = get_data_extractor(sociallogin.account.provider)
    if extractor is not None:
        profile_fields = (
            "username",
            "email",
            "area",
            "city",
            "country",
            "delivery",
            "fax",
            "first_name",
            "last_name",
            "organization",
            "position",
            "profile",
            "voice",
            "zipcode",
        )
        for field in profile_fields:
            try:
                extractor_method = getattr(extractor, f"extract_{field}")
                value = extractor_method(sociallogin.account.extra_data)
                if not user_field(user, field):
                    user_field(user, field, value)
            except (AttributeError, NotImplementedError):
                pass  # extractor doesn't define a method for extracting field
    return user


class LocalAccountAdapter(DefaultAccountAdapter, BaseInvitationsAdapter):
    """Customizations for local accounts

    Check `django-allauth's documentation`_ for more details on this class.

    .. _django-allauth's documentation:
       http://django-allauth.readthedocs.io/en/latest/advanced.html#creating-and-populating-user-instances

    """

    def pre_login(self, request, user, *, email_verification, signal_kwargs, email, signup, redirect_url):

        if email_verification == "mandatory" and not (user.is_superuser or user.is_staff):
            check_result = self.check_user_invalid_email(request, user)
            # None means that the user is valid
            if check_result is not None:
                return check_result

        return super().pre_login(
            request,
            user,
            email_verification=email_verification,
            signal_kwargs=signal_kwargs,
            email=email,
            signup=signup,
            redirect_url=redirect_url,
        )

    def is_open_for_signup(self, request):
        return _site_allows_signup(request)

    def get_login_redirect_url(self, request):
        profile_path = reverse("profile_detail", kwargs={"username": request.user.username})
        return profile_path

    def populate_username(self, request, user):
        # validate the already generated username with django validation
        # if it passes use that, otherwise use django-allauth's way of
        # generating a unique username
        try:
            user.full_clean()
            safe_username = user_username(user)
        except ValidationError:
            safe_username = self.generate_unique_username(
                [user_field(user, "first_name"), user_field(user, "last_name"), user_email(user), user_username(user)]
            )
        user_username(user, safe_username)

    def send_invitation_email(self, email_template, email, context):
        self.send_mail(email_template, email, context)

    def send_mail(self, template_prefix, email, context):
        enh_context = self.enhanced_invitation_context(context)
        msg = self.render_mail(template_prefix, email, enh_context)
        try:
            msg.send()
        except Exception as e:
            logger.exception(e)
            messages.warning(context.get("request"), f"An error occurred while trying to send the email: {e}")

    def enhanced_invitation_context(self, context):
        user = context.get("inviter") if context.get("inviter") else context.get("user")
        enhanced_context = context.copy()
        enhanced_context.update(
            {"MEDIA_URL": settings.MEDIA_URL, "SITEURL": settings.SITEURL, "STATIC_URL": settings.STATIC_URL}
        )
        if user:
            full_name = " ".join((user.first_name, user.last_name)) if user.first_name or user.last_name else None
            user_groups = GroupProfile.objects.filter(
                slug__in=user.groupmember_set.values_list("group__slug", flat=True)
            )
            enhanced_context = context.copy()
            enhanced_context.update(
                {
                    "username": user.username,
                    "inviter_name": full_name or str(user),
                    "inviter_first_name": user.first_name or str(user),
                    "inviter_id": user.id,
                    "groups": user_groups,
                }
            )
        return enhanced_context

    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit=commit)
        if settings.ACCOUNT_APPROVAL_REQUIRED:
            user.is_active = False
            user.save()
        return user

    def respond_user_inactive(self, request, user):
        return _respond_inactive_user(user)

    def check_user_invalid_email(self, request, user):
        return handle_user_invalid_email(user)


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """Customizations for social accounts

    Check `django-allauth's documentation`_ for more details on this class.

    .. _django-allauth's documentation:
         http //django-allauth.readthedocs.io/en/latest/advanced.html#creating-and-populating-user-instances

    """

    def is_open_for_signup(self, request, sociallogin):
        return _site_allows_signup(request)

    def populate_user(self, request, sociallogin, data):
        """This method is called when a new sociallogin is created"""
        user = super().populate_user(request, sociallogin, data)
        update_profile(sociallogin)
        return user

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form=form)
        extractor = get_data_extractor(sociallogin.account.provider)
        try:
            keywords = extractor.extract_keywords(sociallogin.account.extra_data)
            for _kw in keywords:
                user.keywords.add(_kw)
        except (AttributeError, NotImplementedError):
            pass  # extractor doesn't define a method for extracting field
        if settings.ACCOUNT_APPROVAL_REQUIRED:
            user.is_active = False
            user.save()
        return user

    def respond_user_inactive(self, request, user):
        return _respond_inactive_user(user)


def _site_allows_signup(django_request):
    if getattr(settings, "ACCOUNT_OPEN_SIGNUP", True):
        result = True
    else:
        try:
            result = bool(django_request.session.get("account_verified_email"))
        except AttributeError:
            result = False
    return result


def _respond_inactive_user(user):
    return HttpResponseRedirect(reverse("moderator_contacted", kwargs={"inactive_user": user.id}))


def handle_user_invalid_email(user):
    email_regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
    if not user.email or not (re.fullmatch(email_regex, user.email)):
        return HttpResponseRedirect(reverse("moderator_needed"))


PROVIDER_ID = getattr(settings, "SOCIALACCOUNT_OIDC_PROVIDER", "geonode_openid_connect")

ACCESS_TOKEN_URL = getattr(settings, "SOCIALACCOUNT_PROVIDERS", {}).get(PROVIDER_ID, {}).get("ACCESS_TOKEN_URL", "")

AUTHORIZE_URL = getattr(settings, "SOCIALACCOUNT_PROVIDERS", {}).get(PROVIDER_ID, {}).get("AUTHORIZE_URL", "")

PROFILE_URL = getattr(settings, "SOCIALACCOUNT_PROVIDERS", {}).get(PROVIDER_ID, {}).get("PROFILE_URL", "")

ID_TOKEN_ISSUER = getattr(settings, "SOCIALACCOUNT_PROVIDERS", {}).get(PROVIDER_ID, {}).get("ID_TOKEN_ISSUER", "")


class GenericOpenIDConnectAdapter(OAuth2Adapter, SocialAccountAdapter):
    provider_id = PROVIDER_ID
    access_token_url = ACCESS_TOKEN_URL
    authorize_url = AUTHORIZE_URL
    profile_url = PROFILE_URL
    id_token_issuer = ID_TOKEN_ISSUER

    def get_provider(self, request=None, provider=None):
        """Looks up a `provider`, supporting subproviders by looking up by
        `provider_id`.
        """
        from allauth.socialaccount.providers import registry

        request = request or self.request
        provider = provider or self.provider_id
        provider_class = registry.get_class(provider)
        if provider_class is None or provider_class.uses_apps:
            app = self.get_app(request, provider=provider)
            if not provider_class:
                # In this case, the `provider` argument passed was a
                # `provider_id`.
                provider_class = registry.get_class(app.provider)
            if not provider_class:
                raise ImproperlyConfigured(f"unknown provider: {app.provider}")
            return provider_class(request, app=app)
        elif provider_class:
            assert not provider_class.uses_apps
            return provider_class(request, app=None)
        else:
            raise ImproperlyConfigured(f"unknown provider: {app.provider}")

    def complete_login(self, request, app, token, response, **kwargs):
        extra_data = {}
        if self.profile_url:
            try:
                headers = {"Authorization": f"Bearer {token.token}"}
                resp = requests.get(self.profile_url, headers=headers)
                profile_data = resp.json()
                extra_data.update(profile_data)
            except Exception:
                logger.exception(OAuth2Error("Invalid profile_url, falling back to id_token checks..."))
        if "id_token" in response:
            try:
                extra_data_id_token = jwt.decode(
                    response["id_token"],
                    # Since the token was received by direct communication
                    # protected by TLS between this library and Google, we
                    # are allowed to skip checking the token signature
                    # according to the OpenID Connect Core 1.0
                    # specification.
                    # https://openid.net/specs/openid-connect-core-1_0.html#IDTokenValidation
                    options={
                        "verify_signature": False,
                        "verify_iss": True,
                        "verify_aud": True,
                        "verify_exp": True,
                    },
                    issuer=self.id_token_issuer,
                    audience=app.client_id,
                )
                extra_data.update(extra_data_id_token)
            except jwt.PyJWTError as e:
                raise OAuth2Error("Invalid id_token") from e
        login = self.get_provider().sociallogin_from_response(request, extra_data)
        return login

    def save_user(self, request, sociallogin, form=None):
        user = super(SocialAccountAdapter, self).save_user(request, sociallogin, form=form)
        extractor = get_data_extractor(sociallogin.account.provider)
        group_role_mapper = get_group_role_mapper(sociallogin.account.provider)
        try:
            groups = extractor.extract_groups(sociallogin.account.extra_data) or extractor.extract_roles(
                sociallogin.account.extra_data
            )

            # check here if user is member already of other groups and remove it form the ones that are not declared here...
            for groupprofile in user.group_list_all():
                groupprofile.leave(user)
            for group_role_name in groups:
                group_name, role_name = group_role_mapper.parse_group_and_role(group_role_name)
                groupprofile = GroupProfile.objects.filter(slug=group_name).first()
                if groupprofile:
                    groupprofile.join(user)
                    if group_role_mapper.is_manager(role_name):
                        groupprofile.promote(user)
        except (AttributeError, NotImplementedError):
            pass  # extractor doesn't define a method for extracting field
        return user
