from geonode.api.urls import router as geonode_router
from cpt.views import CampaignViewSet, CTPFeedbackViewSet
from rest_framework.routers import DefaultRouter
from django.urls import path, include

router = DefaultRouter( )
router.register('campaigns', CampaignViewSet, basename='campaigns')
router.register('feedback', CTPFeedbackViewSet, basename='feedback')

urlpatterns = [
    path('cpt/', include(router.urls)),
]