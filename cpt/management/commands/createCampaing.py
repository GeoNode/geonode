from django.core.management.base import BaseCommand
from django.utils import timezone
from cpt.models import CategoryType, Category, Campaign

class Command(BaseCommand):
    help = 'Create sample campaigns and categories'

    def handle(self, *args, **kwargs):
        # Create CategoryType for "New Park"
        new_park_type = CategoryType.objects.create(
            name="New Park",
            description="Categories related to feedback on new park projects."
        )
        self.stdout.write(self.style.SUCCESS(f"CategoryType 'New Park' created with ID: {new_park_type.type_id}"))

        # Create Categories under "New Park"
        park_categories = ["Positive", "Negative", "Neutral", "New Suggestion", "Different Suggestion"]
        for category_name in park_categories:
            category = Category.objects.create(
                name=category_name,
                category_type=new_park_type
            )
            self.stdout.write(self.style.SUCCESS(f"Category '{category_name}' created for 'New Park' with ID: {category.category_id}"))

        # Create a Campaign for "New Park"
        park_campaign = Campaign.objects.create(
            campaign_name="Build a New Park",
            campaing_title="New Park Construction",
            campaing_short_description="A campaign to gather feedback on the new park construction project.",
            campaing_detailed_description="We are planning to build a new park in the city. Share your feedback on the proposal.",
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=365),  # 1 year from now
            rate_enabled=True,
            form_enabled=True,
            allow_drawings=True,
            category_type=new_park_type
        )
        self.stdout.write(self.style.SUCCESS(f"Campaign 'New Park' created with ID: {park_campaign.campaign_id}"))

        # Create CategoryType for "New Road"
        new_road_type = CategoryType.objects.create(
            name="New Road",
            description="Categories related to feedback on new road construction."
        )
        self.stdout.write(self.style.SUCCESS(f"CategoryType 'New Road' created with ID: {new_road_type.type_id}"))

        # Create Categories under "New Road"
        road_categories = ["Positive", "Negative", "Neutral", "New Suggestion", "Different Suggestion"]
        for category_name in road_categories:
            category = Category.objects.create(
                name=category_name,
                category_type=new_road_type
            )
            self.stdout.write(self.style.SUCCESS(f"Category '{category_name}' created for 'New Road' with ID: {category.category_id}"))

        # Create a Campaign for "New Road"
        road_campaign = Campaign.objects.create(
            campaign_name="Construct a New Road",
            campaing_title="New Road Development",
            campaing_short_description="A campaign to gather feedback on the new road development project.",
            campaing_detailed_description="We are planning to develop a new road in the city. Share your feedback on the proposal.",
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=365),  # 1 year from now
            rate_enabled=True,
            form_enabled=True,
            allow_drawings=True,
            category_type=new_road_type
        )
        self.stdout.write(self.style.SUCCESS(f"Campaign 'New Road' created with ID: {road_campaign.campaign_id}"))
