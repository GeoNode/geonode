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
from django.core.files.storage import FileSystemStorage

from urllib.parse import urlsplit, urljoin

from geonode.utils import resolve_object
from geonode.layers.models import Layer, LayerFile

register = template.Library()

storage = FileSystemStorage()


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
            upload_session = instance.get_upload_session()
            if upload_session:
                layer_files = [
                    item for item in LayerFile.objects.filter(upload_session=upload_session)]
                if layer_files:
                    for lyr in layer_files:
                        if not storage.exists(str(lyr.file)):
                            return False
        except Exception:
            traceback.print_exc()
            return False
    if layer_files:
        return True
    else:
        return False
