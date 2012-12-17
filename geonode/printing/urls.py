from django.conf.urls.defaults import patterns, url

urlpatterns = patterns(
    'geonode.printing.views',

    url(r'^templates$',
        'printing_template_list', name='printing_templates'
        ),

    url(r'^print/(?P<templateid>\d+)/(?P<mapid>\d+)$',
        'printing_print_map',
        name='printing_map'
        ),

    url(r'^print/layer/(?P<templateid>\d+)/(?P<layerid>\d+)$',
        'printing_print_layer',
        name='printing_layer'
        ),

    url(r'^preview/(?P<templateid>\d+)/(?P<mapid>\d+)$',
        'printing_preview_map',
        name='printing_preview_map'
        ),

    url(r'^preview/(?P<templateid>\d+)/(?P<layerid>\w+:\w+)$',
        'printing_preview_layer',
        name='printing_preview_layer'
        ),
)
