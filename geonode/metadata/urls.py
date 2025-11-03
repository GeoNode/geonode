from geonode.metadata.api.urls import urlpatterns
from geonode.api.urls import router
from .api import views

router.register(r"metadata", views.MetadataViewSet, "metadata")
urlpatterns += []  # make flake8 happy
