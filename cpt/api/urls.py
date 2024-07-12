from django.urls import include, path
from rest_framework.routers import DefaultRouter
from cpt.api.views import CampaignListView,CampaignViewSet

router = DefaultRouter()
router.register('campaigns', CampaignListView, basename='campaigns-list')
router.register('curl', CampaignViewSet, basename='campaigns')
# router.register('campaigns/<str:campaign_url_name>', CampaignDetailByURLNameView, basename='campaign-url-name')

urlpatterns = [
    path('cpt/', include(router.urls)),
]
