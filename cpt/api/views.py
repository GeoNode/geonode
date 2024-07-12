from rest_framework import viewsets
from rest_framework import generics
from rest_framework.decorators import action
from rest_framework.response import Response
from cpt.models import Campaign
from cpt.api.serializers import CampaignSerializer,CampaignsListSerializer
from rest_framework.exceptions import NotFound

class CampaignListView(viewsets.ReadOnlyModelViewSet):
    """
    Show all campaigns with their basic information
    """
    queryset = Campaign.objects.all()
    serializer_class = CampaignsListSerializer


class CampaignViewSet(viewsets.ModelViewSet):
    queryset = Campaign.objects.all()
    serializer_class = CampaignSerializer
    http_method_names = ['get', 'head', 'options']  #

    @action(detail=False, methods=['get'], url_path='(?P<campaign_url_name>[^/.]+)')
    def get_by_url_name(self, request, campaign_url_name=None):
        try:
            campaign = Campaign.objects.get(campaign_url_name=campaign_url_name)
            serializer = self.get_serializer(campaign)
            return Response(serializer.data)
        except Campaign.DoesNotExist:
            raise NotFound(f"Campaign with URL name {campaign_url_name} not found")