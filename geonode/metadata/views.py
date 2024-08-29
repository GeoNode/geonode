import json

from geonode.base.models import ResourceBase
from geonode.metadata.serializer import MetadataModelSerializer
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.response import Response
from rest_framework import generics
from geonode.metadata import metadata_path


class DynamicResourceViewSet(ReadOnlyModelViewSet):
    """
    A simple ViewSet for listing or retrieving users.
    """

    serializer_class = MetadataModelSerializer
    queryset = ResourceBase.objects.all()  # TODO to be replaced with metadata model

    def list(self, request):
        serializer = self.serializer_class(self.queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        serializer = self.serializer_class(self.queryset.first())
        return Response(serializer.data)


class UiSchemaViewset(generics.RetrieveAPIView):
    """
    Return the UI schema
    """

    def get(self, request, **kwargs):
        with open(f"{metadata_path}/ui_schema.json", "r") as f:
            ui_schema = json.load(f)
        return Response(ui_schema)
