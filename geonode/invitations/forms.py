#########################################################################
#
# Copyright (C) 2018 OSGeo
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
from django.utils.translation import ugettext as _
from django.contrib.auth import get_user_model

from invitations.adapters import get_invitations_adapter
from invitations.exceptions import AlreadyInvited, AlreadyAccepted, UserRegisteredEmail
from invitations.utils import get_invitation_model

Invitation = get_invitation_model()


class CleanEmailMixin:

    def validate_invitation(self, email):
        if Invitation.objects.all_valid().filter(
                email__iexact=email, accepted=False):
            raise AlreadyInvited
        elif Invitation.objects.filter(
                email__iexact=email, accepted=True):
            raise AlreadyAccepted
        elif get_user_model().objects.filter(email__iexact=email):
            raise UserRegisteredEmail
        else:
            return True

    def clean_email(self):
        emails = self.cleaned_data["email"]
        emails = emails.replace(";", ",").split(",")
        for em in emails:
            email = get_invitations_adapter().clean_email(em.strip())

            errors = {
                "already_invited": _(f"The e-mail address '{email}' has already been invited."),
                "already_accepted": _(f"The e-mail address '{email}' has already accepted an invite."),
                "email_in_use": _(f"An active user is already using the e-mail address '{email}'"),
            }
            try:
                self.validate_invitation(email)
            except AlreadyInvited:
                raise forms.ValidationError(errors["already_invited"])
            except AlreadyAccepted:
                raise forms.ValidationError(errors["already_accepted"])
            except UserRegisteredEmail:
                raise forms.ValidationError(errors["email_in_use"])

        return emails


class GeoNodeInviteForm(forms.Form, CleanEmailMixin):

    email = forms.CharField(
        label=_("E-mail"),
        required=True,
        widget=forms.TextInput(
            attrs={"type": "text", "size": "1200"}), initial="")

    def save(self, emails):
        invitations = []
        for em in emails:
            invitations.append(Invitation.create(email=em.strip()))
        return invitations
