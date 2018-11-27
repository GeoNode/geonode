# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
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

try:
    import json
except ImportError:
    from django.utils import simplejson as json
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.contrib.auth import get_user_model

from geonode.utils import resolve_object
from geonode.base.models import ResourceBase
from geonode.layers.models import Layer
from geonode.people.models import Profile

if "notification" in settings.INSTALLED_APPS:
    from notification import models as notification


def _perms_info(obj):
    info = obj.get_all_level_info()

    return info


def _perms_info_json(obj):
    info = _perms_info(obj)
    info['users'] = dict([(u.username, perms)
                          for u, perms in info['users'].items()])
    info['groups'] = dict([(g.name, perms)
                           for g, perms in info['groups'].items()])

    return json.dumps(info)


@require_POST
def request_permissions(request):
    """ Request permission to download a resource.
    """
    uuid = request.POST['uuid']
    resource = get_object_or_404(ResourceBase, uuid=uuid)
    try:
        notification.send(
            [resource.owner],
            'request_download_resourcebase',
            {'from_user': request.user, 'resource': resource}
        )
        return HttpResponse(
            json.dumps({'success': 'ok', }),
            status=200,
            content_type='text/plain')
    except BaseException:
        return HttpResponse(
            json.dumps({'error': 'error delivering notification'}),
            status=400,
            content_type='text/plain')


def send_email_consumer(layer_uuid, user_id):
    resource = get_object_or_404(ResourceBase, uuid=layer_uuid)
    user = Profile.objects.get(id=user_id)
    notification.send(
        [resource.owner],
        'request_download_resourcebase',
        {'from_user': user, 'resource': resource}
    )


def send_email_owner_on_view(owner, viewer, layer_id, geonode_email="email@geo.node"):
    # get owner and viewer emails
    owner_email = get_user_model().objects.get(username=owner).email
    layer = Layer.objects.get(id=layer_id)
    # check if those values are empty
    if owner_email and geonode_email:
        from django.core.mail import send_mail
        # TODO: Copy edit message.
        subject_email = "Your Layer has been seen."
        msg = ("Your layer called {0} with uuid={1}"
               " was seen by {2}").format(layer.name, layer.uuid, viewer)
        try:
            send_mail(subject_email, msg, geonode_email, [owner_email, ])
        except BaseException:
            pass
