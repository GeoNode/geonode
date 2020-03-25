# -*- coding: utf-8 -*-
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
import traceback

from django.contrib.sites.models import Site
try:
    from django.urls import reverse
except ImportError:
    from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required

from .forms import GeoNodeInviteForm
from invitations import signals
from invitations.views import SendInvite
from invitations.utils import get_invitation_model
from invitations.adapters import get_invitations_adapter
from geonode.decorators import view_decorator

Invitation = get_invitation_model()


@view_decorator(login_required, subclass=True)
class GeoNodeSendInvite(SendInvite):
    template_name = 'invitations/forms/_invite.html'
    form_class = GeoNodeInviteForm

    def __init__(self, *args, **kwargs):
        super(SendInvite, self).__init__(*args, **kwargs)

    def form_valid(self, form):
        emails = form.cleaned_data["email"]
        invited = []

        invite = None
        try:
            invites = form.save(emails)
            for invite_obj in invites:
                invite = invite_obj
                invite.inviter = self.request.user
                invite.save()
                # invite.send_invitation(self.request)
                self.send_invitation(invite, self.request)
                invited.append(invite_obj.email)
        except Exception as e:
            traceback.print_exc()
            if invite:
                invite.delete()
            return self.form_invalid(form, emails, e)

        return self.render_to_response(
            self.get_context_data(
                success_message=_("Invitations succefully sent to '%(email)s'") % {
                    "email": ', '.join(invited)}))

    def form_invalid(self, form, emails=None, e=None):
        if e:
            return self.render_to_response(
                self.get_context_data(
                    error_message=_("Sorry, it was not possible to invite '%(email)s'"
                                    " due to the following isse: %(error)s (%(type)s)") % {
                        "email": emails, "error": str(e), "type": type(e)}))
        else:
            return self.render_to_response(
                self.get_context_data(form=form))

    def send_invitation(self, invite, request, **kwargs):
        current_site = kwargs.pop('site', Site.objects.get_current())
        invite_url = reverse('geonode.invitations:accept-invite',
                             args=[invite.key])
        invite_url = request.build_absolute_uri(invite_url)
        ctx = kwargs
        ctx.update({
            'invite_url': invite_url,
            'site_name': current_site.name,
            'email': invite.email,
            'key': invite.key,
            'inviter': invite.inviter,
        })

        email_template = 'invitations/email/email_invite'
        adapter = get_invitations_adapter()
        adapter.send_invitation_email(email_template, invite.email, ctx)
        invite.sent = timezone.now()
        invite.save()

        signals.invite_url_sent.send(
            sender=invite.__class__,
            instance=invite,
            invite_url_sent=invite_url,
            inviter=invite.inviter)
