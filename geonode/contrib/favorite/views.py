import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response
from django.template import RequestContext

from geonode.documents.models import Document
from geonode.layers.models import Layer
from geonode.maps.models import Map
import models


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
    return render_to_response(
        "favorite/favorite_list.html",
        RequestContext(
            req,
            {'favorites': models.Favorite.objects.favorites_for_user(req.user), }
        )
    )
