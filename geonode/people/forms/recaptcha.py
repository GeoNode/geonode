#########################################################################
#
# Copyright (C) 2019 Open Source Geospatial Foundation - all rights reserved
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

from django import forms
from allauth.account.forms import LoginForm

try:
    from captcha.fields import ReCaptchaField
except ImportError:
    from django_recaptcha.fields import ReCaptchaField


class AllauthReCaptchaSignupForm(forms.Form):
    captcha = ReCaptchaField(label=False)

    def signup(self, request, user):
        """Required, or else it thorws deprecation warnings"""
        pass


class AllauthRecaptchaLoginForm(LoginForm):
    captcha = ReCaptchaField(label=False)

    def login(self, *args, **kwargs):
        return super(AllauthRecaptchaLoginForm, self).login(*args, **kwargs)
