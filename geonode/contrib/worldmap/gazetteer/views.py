import json
from dicttoxml import dicttoxml

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

from geonode.layers.views import _resolve_layer

from .utils import add_to_gazetteer, getGazetteerResults, getGazetteerEntry, getExternalServiceResults
from .models import GazetteerAttribute


def search(request, place_name, map=None, layer=None,
           start_date=None, end_date=None, project=None, services=None,
           user=None, format='json'):
    """
    Search the Gazetteer and return results in JSON or XML format.
    """
    if not format:
        out_format = 'json'
    else:
        out_format = format.lower()
    if out_format not in ('xml', 'json'):
        out_format = 'json'

    if place_name.isdigit():
        posts = getGazetteerEntry(place_name)
    else:
        posts = getGazetteerResults(place_name, map, layer, start_date, end_date, project, user)
    if services is not None:
        posts.extend(getExternalServiceResults(place_name, services))
    if out_format == 'json':
        return HttpResponse(json.dumps(posts, sort_keys=True, indent=4),
                            content_type="application/json")
    elif out_format == 'xml':
        return HttpResponse(dicttoxml([{'resource': post} for post in posts], attr_type=False, custom_root='response'),
                            content_type="application/xml")


@login_required
def edit_layer_gazetteer(
        request,
        layername):
    """
    Manage the layer in the gazetteer.
    """

    def set_none_if_empty(str):
        if len(str) == 0:
            return None
        return str

    layer = _resolve_layer(
        request,
        layername,
        'base.change_resourcebase_metadata',
        'permissions message from grazetteer')

    status_message = None
    if request.method == 'POST':
        status_message = ''
        gazetteer_name = set_none_if_empty(request.POST.get('gazetteer-name', ''))
        start_attribute = set_none_if_empty(request.POST.get('start-attribute', ''))
        end_attribute = set_none_if_empty(request.POST.get('end-attribute', ''))
        sel_start_date_format = set_none_if_empty(request.POST.get('sel-start-date-format', ''))
        sel_end_date_format = set_none_if_empty(request.POST.get('sel-end-date-format', ''))
        attributes_list = request.POST.getlist('attributes')
        for attribute in layer.attributes:
            if attribute.attribute in attributes_list:
                print 'Adding %s to gazetteer...' % attribute
                gaz_att, created = GazetteerAttribute.objects.get_or_create(attribute=attribute)
                gaz_att.in_gazetteer = True
                if start_attribute == attribute.attribute:
                    gaz_att.is_start_date = True
                    gaz_att.date_format = sel_start_date_format
                if end_attribute == attribute.attribute:
                    gaz_att.is_end_date = True
                    gaz_att.date_format = sel_end_date_format
                gaz_att.save()
                status_message += ' %s' % attribute.attribute
            else:
                print 'Removing %s from gazetteer...' % attribute
                gaz_att, created = GazetteerAttribute.objects.get_or_create(attribute=attribute)
                gaz_att.in_gazetteer = False
                gaz_att.save()
        # now update the gazetteer
        # TODO use Celery for this
        add_to_gazetteer(layer,
                         attributes_list,
                         start_attribute,
                         end_attribute,
                         gazetteer_name,
                         request.user.username)

    gazetteer_attributes = []
    for attribute in layer.attributes:
        if hasattr(attribute, 'gazetteerattribute'):
            attribute.in_gazetteer = attribute.gazetteerattribute.in_gazetteer
        else:
            attribute.in_gazetteer = False
        gazetteer_attributes.append(attribute)
    template = 'gazetteer/edit_layer_gazetteer.html'

    return render(request, template, {
        "layer": layer,
        "gazetteer_attributes": gazetteer_attributes,
        "status_message": status_message,
    })
