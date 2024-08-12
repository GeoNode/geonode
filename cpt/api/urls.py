from geonode.api.urls import router
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action

class PlaceholderViewSet(viewsets.ModelViewSet):
    """
    A placeholder viewset to simulate an endpoint in the API documentation.
    """

    @action(detail=False, methods=['get'])
    def list(self, request):
        return Response({"detail": "This is a placeholder endpoint for documentation purposes."})

# Registering the placeholder viewset for documentation purposes
router.register(r'cpt2', PlaceholderViewSet, 'cpt')

urlpatterns = []
