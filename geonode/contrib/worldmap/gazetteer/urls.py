from django.conf.urls import url
from .views import search, edit_layer_gazetteer

urlpatterns = [
    url(
        r'^gazetteer/edit/(?P<layername>[^/]*)$',
        edit_layer_gazetteer,
        name='edit_layer_gazetteer'
    ),
    url(r'^gazetteer/(?P<place_name>[^/]+)' +
        r'(/Service/(?P<services>[\w\,]+))?' +
        '(/Project/(?P<project>[A-Za-z0-9_-]+))?' +
        r'(/Map/(?P<map>[\d]+))?' +
        '(/Layer/(?P<layer>[A-Za-z0-9_-]+))?' +
        r'(/StartDate/(?P<start_date>[\d\s\/\-\:]+(\sBC|\sAD)?))?' +
        r'(/EndDate/(?P<end_date>[\d\s\/\-\:]+(\sBC|\sAD)?))?' +
        '(/User/(?P<user>[A-Za-z0-9_-]+))?' +
        '(/(?P<format>(json|xml)))?$', search),
]
