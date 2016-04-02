from geonode.gazetteer.handlers import DjangoAuthentication
from django.conf.urls.defaults import *
from piston.resource import Resource


from geonode.gazetteer.handlers import PlaceNameHandler

auth = DjangoAuthentication()
ad = { 'authentication': auth }


placename_resource = Resource(handler=PlaceNameHandler)

urlpatterns = patterns('',
    url(r'^(?P<place_name>\d)$', placename_resource),
    url(r'^(?P<place_name>\d)/xml$', placename_resource, { 'emitter_format': 'xml' }),
    url(r'^(?P<place_name>\d)/json', placename_resource, { 'emitter_format': 'json' }),

    url(r'^(?P<place_name>[^/]+)' +
        '(/Service/(?P<services>[\w\,]+))?' +
        '(/Project/(?P<project>[A-Za-z0-9_-]+))?' +
        '(/Map/(?P<map>[\d]+))?' +
        '(/Layer/(?P<layer>[A-Za-z0-9_-]+))?' +
        '(/StartDate/(?P<start_date>[\d\s\/\-\:]+(\sBC|\sAD)?))?' +
        '(/EndDate/(?P<end_date>[\d\s\/\-\:]+(\sBC|\sAD)?))?' +
        '(/User/(?P<user>[A-Za-z0-9_-]+))?' +
        '$', placename_resource),

    url(r'^(?P<place_name>[^/]+)' +
        '(/Service/(?P<services>[\w\,]+))?' +
        '(/Project/(?P<project>[A-Za-z0-9_-]+))?' +
        '(/Map/(?P<map>[\d]+))?' +
        '(/Layer/(?P<layer>[A-Za-z0-9_-]+))?' +
        '(/StartDate/(?P<start_date>[\d\s\/\-\:]+(\sBC|\sAD)?))?' +
        '(/EndDate/(?P<end_date>[\d\s\/\-\:]+(\sBC|\sAD)?))?' +
        '(/User/(?P<user>[A-Za-z0-9_-]+))?' +
        '/xml$', placename_resource,  { 'emitter_format': 'xml' }),

    url(r'^(?P<place_name>[^/]+)' +
        '(/Service/(?P<services>[\w\,]+))?' +
        '(/Project/(?P<project>[A-Za-z0-9_-]+))?' +
        '(/Map/(?P<map>[\d]+))?' +
        '(/Layer/(?P<layer>[A-Za-z0-9_-]+))?' +
        '(/StartDate/(?P<start_date>[\d\s\/\-\:]+(\sBC|\sAD)?))?' +
        '(/EndDate/(?P<end_date>[\d\s\/\-\:]+(\sBC|\sAD)?))?' +
        '(/User/(?P<user>[A-Za-z0-9_-]+))?' +
        '/json$', placename_resource, { 'emitter_format': 'json' }),



)
