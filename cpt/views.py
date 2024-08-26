from rest_framework import viewsets,mixins, status
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.exceptions import NotFound
#add below for authentication and permissions.
# from rest_framework.permissions import IsAuthenticatedOrReadOnly
# from rest_framework.authentication import SessionAuthentication, BasicAuthentication
# from oauth2_provider.contrib.rest_framework import OAuth2Authentication

from django.utils import timezone
from django.urls import reverse
from django.shortcuts import get_object_or_404
from cpt.models import Campaign, Form, Rating

from cpt.models import Campaign, Form, Rating
from cpt.serializers import CampaignSerializer,CampaignsListSerializer,FormSerializer, RatingSerializer


class CampaignViewSet(viewsets.ModelViewSet):
    """
    # nice to have : campaign liste nokta verisi ekleyebilirsek campaign list yaparken ekranda toplam nokta sayısını gösterebiliriz.

    CampaignCountViewSet buraya alacaz
    
    """
    queryset = Campaign.objects.all()
    http_method_names = ['get', 'head', 'options']

    def get_queryset(self):
        now = timezone.now()
        return Campaign.objects.filter(end_date__gt=now, start_date__lte=now)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CampaignsListSerializer
        return CampaignSerializer

    @action(detail=False, methods=['get'], url_path='(?P<campaign_url_name>[^/.]+)')
    def get_by_url_name(self, request, campaign_url_name=None):
        try:
            campaign = Campaign.objects.get(campaign_url_name=campaign_url_name)
            serializer = self.get_serializer(campaign)
            return Response(serializer.data)
        except Campaign.DoesNotExist:
            raise NotFound(f"Campaign with URL name {campaign_url_name} not found")

class CTPFeedbackViewSet(viewsets.ViewSet):

    # For future we might want to add authentication and permissions for post request
    # authentication_classes = [SessionAuthentication, BasicAuthentication, OAuth2Authentication]
    # permission_classes = [IsAuthenticatedOrReadOnly]
    """
    A ViewSet for handling feedback and ratings.
    """

    def get_serializer_class(self):
        """
        Return the appropriate serializer class based on the request data.
        """
        data_type = self.request.data.get('type')
        if data_type == 'POST1':
            return RatingSerializer
        elif data_type in ['POST2', 'POST3']:
            return FormSerializer
        raise ValidationError({"error": "Invalid type provided, cannot determine serializer."})

    def create(self, request, *args, **kwargs):
        data_type = request.data.get('type')

        if data_type == 'POST1':
            # Only rating
            serializer = RatingSerializer(data=request.data.get('rating'))
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif data_type == 'POST2':
            # Only feedback
            feedback_data = request.data.get('feedback')
            serializer = FormSerializer(data=feedback_data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif data_type == 'POST3':
            # Feedback + rating
            feedback_data = request.data.get('feedback')
            rating_data = request.data.get('rating')

            # Save feedback first
            feedback_serializer = FormSerializer(data=feedback_data)
            if feedback_serializer.is_valid():
                feedback_obj = feedback_serializer.save()

                # Save rating with reference to the feedback
                rating_data['form'] = feedback_obj.id
                rating_serializer = RatingSerializer(data=rating_data)
                if rating_serializer.is_valid():
                    rating_serializer.save()
                    return Response(
                        {"feedback": feedback_serializer.data, "rating": rating_serializer.data},
                        status=status.HTTP_201_CREATED
                    )
                return Response(rating_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            return Response(feedback_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response({"error": "Invalid type provided."}, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        """

        GET method to return information on how to use the POST endpoint.
        """
        post1_structure = {
            "type": "POST1",
            "rating": {
                "campaign_id": 1,
                "rating": 3,
            }
        }
        post2_structure = {
            "type": "POST2",
            "feedback": {
                "campaign_id": 1,
                "feedback_location": "Point",  # example: "POINT(1.0 1.0)"
                "feedback_text": "Your feedback here",
                "feedback_category": "general",
                "feedback_geometry": "GeoJSON string"
            }
        }
        post3_structure = {
            "type": "POST3",
            "rating": {
                "campaign_id": 1,
                "rating": 3,
            },
            "feedback": {
                "campaign_id": 1,
                "feedback_location": "Point",  # example: "POINT(1.0 1.0)"
                "feedback_text": "Your feedback here",
                "feedback_category": "general",
                "feedback_geometry": "GeoJSON string"
            }
        }
        return Response({
            "UPDATA DOCSSSSSS!!!!!!!!!!!": "This endpoint is used to provide feedback and ratings for campaigns.",
            "POST1": post1_structure,
            "POST2": post2_structure,
            "POST3": post3_structure
        }, status=status.HTTP_200_OK)
    
"""
class CampaignCountViewSet(viewsets.ViewSet):
    # We will check and delete this viewset later
    def retrieve(self, request, pk=None):
        campaign = get_object_or_404(Campaign, campaign_id=pk)
        unique_form_ids = Form.objects.filter(campaign=campaign).values_list('id', flat=True)
        rating_count_without_form = Rating.objects.filter(campaign=campaign, form__isnull=True).count()
        total_comment_count = len(unique_form_ids) + rating_count_without_form
        return Response({"campaign_id": pk, "comment_count": total_comment_count}, status=status.HTTP_200_OK)

    def list(self, request):
        # Son 5 kampanyayı getiriyoruz
        last_campaigns = Campaign.objects.order_by('-campaign_id')[:5]
        campaigns_data = []

        for campaign in last_campaigns:
            # Her kampanya için ID ve isimle beraber bir URL oluşturuyoruz
            detail_url = reverse('campaign-comments-count-detail', kwargs={'pk': campaign.campaign_id})
            campaigns_data.append({
                'id': campaign.campaign_id,
                'name': campaign.campaign_name,
                'detail_url': detail_url
            })

        return Response(campaigns_data, status=status.HTTP_200_OK)
"""
# end of cpt/views.py