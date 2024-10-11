from django.urls import re_path
from geonode.metadata.views import get_schema


urlpatterns = [
    re_path(r"^metadata/schema/$", get_schema, name="get_schema"),
]