from django.urls import include, path
from rest_framework.routers import DefaultRouter
from cpt.api.views import CampaignViewSet

router = DefaultRouter()
router.register('campaigns', CampaignViewSet, basename='campaigns')
# router.register('campaigns/<str:campaign_url_name>', CampaignDetailByURLNameView, basename='campaign-url-name')

urlpatterns = [
    path('cpt/', include(router.urls)),
]
