# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2019 OSGeo
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

from django import template
from django.conf import settings
from django.urls import reverse
from django.utils.translation import ugettext as _
from geonode.storage.manager import storage_manager

from urllib.parse import urlsplit, urljoin

from geonode.layers.models import Layer
from geonode.upload.models import Upload
from geonode.utils import resolve_object

register = template.Library()


@register.simple_tag(takes_context=True)
def original_link_available(context, resourceid, url):
    _not_permitted = _("You are not permitted to save or edit this resource.")
    request = context['request']
    instance = resolve_object(
        request,
        Layer,
        {'pk': resourceid},
        permission='base.download_resourcebase',
        permission_msg=_not_permitted)

    download_url = urljoin(settings.SITEURL, reverse("download", args={resourceid}))
    if urlsplit(url).netloc != urlsplit(download_url).netloc or \
            urlsplit(url).path != urlsplit(download_url).path:
        return True

    layer_files = []
    if isinstance(instance, Layer):
        try:
            upload_session = Upload.objects.get(layer=instance)
            for lyr in upload_session.uploadfile_set.all():
                layer_files.append(lyr)
                if not storage_manager.exists(lyr.file):
                    return False
        except Exception:
            traceback.print_exc()
            return False
    if layer_files:
        return True
    else:
        return False
