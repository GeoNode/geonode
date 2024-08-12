from geonode.api.urls import router as geonode_router
from cpt.views import CampaignViewSet, CTPFeedbackViewSet, CampaignCountViewSet
from rest_framework.routers import DefaultRouter
from django.urls import path, include, re_path

router = DefaultRouter()
router.register('campaigns', CampaignViewSet, basename='campaigns')
router.register('feedback', CTPFeedbackViewSet, basename='feedback')
router.register('campaign-comments-count', CampaignCountViewSet, basename='campaign-comments-count')

urlpatterns = [
    path('cpt/', include(router.urls)),
]
