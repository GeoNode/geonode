# -*- coding: utf-8 -*-
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

from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.utils import user_field
from allauth.account.utils import user_email
from allauth.account.utils import user_username
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

from invitations.adapters import BaseInvitationsAdapter

from django.conf import settings
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.utils.module_loading import import_string
# from django.contrib.auth.models import Group
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
            "zipcode"
        )
        for field in profile_fields:
            try:
                extractor_method = getattr(
                    extractor, f"extract_{field}")
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

    def is_open_for_signup(self, request):
        return _site_allows_signup(request)

    def get_login_redirect_url(self, request):
        profile_path = reverse(
            "profile_detail", kwargs={"username": request.user.username})
        return profile_path

    def populate_username(self, request, user):
        # validate the already generated username with django validation
        # if it passes use that, otherwise use django-allauth's way of
        # generating a unique username
        try:
            user.full_clean()
            safe_username = user_username(user)
        except ValidationError:
            safe_username = self.generate_unique_username([
                user_field(user, 'first_name'),
                user_field(user, 'last_name'),
                user_email(user),
                user_username(user)
            ])
        user_username(user, safe_username)

    def send_invitation_email(self, email_template, email, context):
        enh_context = self.enhanced_invitation_context(context)
        self.send_mail(email_template, email, enh_context)

    def enhanced_invitation_context(self, context):
        user = context.get("inviter") if context.get("inviter") else context.get("user")
        full_name = " ".join((user.first_name, user.last_name)) if user.first_name or user.last_name else None
        user_groups = GroupProfile.objects.filter(
            slug__in=user.groupmember_set.all().values_list("group__slug", flat=True))
        enhanced_context = context.copy()
        enhanced_context.update({
            "username": user.username,
            "inviter_name": full_name or str(user),
            "inviter_first_name": user.first_name or str(user),
            "inviter_id": user.id,
            "groups": user_groups,
            "MEDIA_URL": settings.MEDIA_URL,
            "SITEURL": settings.SITEURL,
            "STATIC_URL": settings.STATIC_URL
        })
        return enhanced_context

    def save_user(self, request, user, form, commit=True):
        user = super(LocalAccountAdapter, self).save_user(
            request, user, form, commit=commit)
        if settings.ACCOUNT_APPROVAL_REQUIRED:
            user.is_active = False
            user.save()
        return user

    def respond_user_inactive(self, request, user):
        return _respond_inactive_user(user)


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
        user = super(SocialAccountAdapter, self).populate_user(
            request, sociallogin, data)
        update_profile(sociallogin)
        return user

    def save_user(self, request, sociallogin, form=None):
        user = super(SocialAccountAdapter, self).save_user(
            request, sociallogin, form=form)
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
    return HttpResponseRedirect(
        reverse("moderator_contacted", kwargs={"inactive_user": user.id})
    )
