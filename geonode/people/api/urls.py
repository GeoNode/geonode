from geonode.people.api import views
from geonode.api.urls import router


router.register("users", views.UserViewSet, "users")

urlpatterns = []
