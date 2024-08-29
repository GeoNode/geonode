from django.urls import path

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from drf_spectacular.renderers import OpenApiJsonRenderer
from geonode.metadata.views import DynamicResourceViewSet, UiSchemaViewset

metadata_url = path("", DynamicResourceViewSet.as_view(actions={"get": "list"}), name="dynamic")

urlpatterns = [
    path(
        "schema/",
        SpectacularAPIView.as_view(patterns=[metadata_url], renderer_classes=[OpenApiJsonRenderer]),
        name="schema",
    ),
    path("schema/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("ui-schema", UiSchemaViewset.as_view(), name="ui_schema"),
    metadata_url,
]
