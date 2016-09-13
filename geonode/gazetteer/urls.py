from django.conf.urls.defaults import *
from geonode.gazetteer.views import search

urlpatterns = patterns('',
    url(r'^(?P<place_name>[^/]+)' +
        '(/Service/(?P<services>[\w\,]+))?' +
        '(/Project/(?P<project>[A-Za-z0-9_-]+))?' +
        '(/Map/(?P<map>[\d]+))?' +
        '(/Layer/(?P<layer>[A-Za-z0-9_-]+))?' +
        '(/StartDate/(?P<start_date>[\d\s\/\-\:]+(\sBC|\sAD)?))?' +
        '(/EndDate/(?P<end_date>[\d\s\/\-\:]+(\sBC|\sAD)?))?' +
        '(/User/(?P<user>[A-Za-z0-9_-]+))?' +
        '(/(?P<format>(json|xml)))?$', search)
)
