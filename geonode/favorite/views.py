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

import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render

from geonode.geoapps.models import GeoApp
from geonode.documents.models import Document
from geonode.layers.models import Layer
from geonode.maps.models import Map
from . import models


@login_required
def favorite(req, subject, id):
    """
    create favorite and put favorite_info object in response.
    method is idempotent, Favorite's create_favorite method
    only creates if does not already exist.
    """
    if subject == 'document':
        obj = get_object_or_404(Document, pk=id)
    elif subject == 'map':
        obj = get_object_or_404(Map, pk=id)
    elif subject == 'layer':
        obj = get_object_or_404(Layer, pk=id)
    elif subject == 'geoapp':
        obj = get_object_or_404(GeoApp, pk=id)
    elif subject == 'user':
        obj = get_object_or_404(settings.AUTH_USER_MODEL, pk=id)

    favorite = models.Favorite.objects.create_favorite(obj, req.user)
    delete_url = reverse("delete_favorite", args=[favorite.pk])
    response = {"has_favorite": "true", "delete_url": delete_url}

    return HttpResponse(json.dumps(response), content_type="application/json", status=200)


@login_required
def delete_favorite(req, id):
    """
    delete favorite and put favorite_info object in response.
    method is idempotent, if favorite does not exist, just return favorite_info.
    """
    try:
        favorite = models.Favorite.objects.get(user=req.user, pk=id)
        favorite.delete()
    except ObjectDoesNotExist:
        pass

    response = {"has_favorite": "false"}

    return HttpResponse(json.dumps(response), content_type="application/json", status=200)


@login_required
def get_favorites(req):
    """
    Display the request user's favorites.
    """
    return render(
        req,
        "favorite/favorite_list.html",
        context={'favorites': models.Favorite.objects.favorites_for_user(req.user), }
    )
