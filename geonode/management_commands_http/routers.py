from rest_framework import routers

from geonode.management_commands_http.views import ManagementCommandJobViewSet


router = routers.DefaultRouter()
router.register("jobs", ManagementCommandJobViewSet, basename="job")
