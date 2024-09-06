from geonode.upload.api.urls import urlpatterns
from geonode.upload.api.views import ResourceImporter, ImporterViewSet
from django.urls import re_path

urlpatterns.insert(
    0,
    re_path(
        r"uploads/upload",
        ImporterViewSet.as_view({"post": "create"}),
        name="importer_upload",
    ),
)

urlpatterns.insert(
    1,
    re_path(
        r"resources/(?P<pk>\w+)/copy",
        ResourceImporter.upload.as_view({"put": "copy"}),
        name="importer_resource_copy",
    ),
)
