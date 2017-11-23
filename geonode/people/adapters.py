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

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.module_loading import import_string

from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.utils import user_field
from allauth.account.utils import sync_user_email_addresses
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

logger = logging.getLogger(__name__)


def get_data_extractor(provider_name):
    """Get the relevant profile extractor instance for the provider

    Retrieve the data extractor instance to use for getting profile
    information from social account providers.

    """

    extractors = getattr(settings, "SOCIALACCOUNT_PROFILE_EXTRACTORS", {})
    extractor_path = extractors.get(provider_name)
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
                extractor_method = getattr(
                    extractor, "extract_{}".format(field))
                value = extractor_method(sociallogin.account.extra_data)
                user_field(user, field, value)
            except (AttributeError, NotImplementedError):
                pass  # extractor doesn't define a method for extracting field
    return user


class LocalAccountAdapter(DefaultAccountAdapter):
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

    def save_user(self, request, user, form, commit=True):
        user = super(LocalAccountAdapter, self).save_user(
            request, user, form, commit=commit)
        if settings.ACCOUNT_APPROVAL_REQUIRED:
            user.is_active = False
            user.save()
        sync_user_email_addresses(user)
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
        print("Populating user...")
        update_profile(sociallogin)
        return user

    def save_user(self, request, sociallogin, form=None):
        user = super(SocialAccountAdapter, self).save_user(
            request, sociallogin, form=form)
        if settings.ACCOUNT_APPROVAL_REQUIRED:
            user.is_active = False
            user.save()
        sync_user_email_addresses(user)
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
