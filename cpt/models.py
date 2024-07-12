from django.db import models
from django.core.validators import RegexValidator

class CategoryType(models.Model):
    type_id = models.AutoField(primary_key=True)  # Auto-generated ID
    name = models.CharField(max_length=100, unique=True, null=True, blank=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Category(models.Model):
    category_id = models.AutoField(primary_key=True)  # Auto-generated ID
    name = models.CharField(max_length=100, null=True, blank=True)
    category_type = models.ForeignKey(CategoryType, on_delete=models.CASCADE, related_name='categories', null=True, blank=True)

    def __str__(self):
        return self.name

class Campaign(models.Model):
    campaign_id = models.AutoField(primary_key=True)  # Auto-generated ID
    campaign_name = models.CharField(max_length=255, null=True, blank=True)
    campaign_url_name = models.CharField(max_length=30, unique=True, validators=[
        RegexValidator(regex=r'^[a-z0-9\-_]+$', message='Only lowercase letters, numbers, hyphens, and underscores allowed.')
    ], null=True, blank=True)
    allow_drawings = models.BooleanField(default=True, null=True, blank=True)
    rate_enabled = models.BooleanField(default=True, null=True, blank=True)  # Changed rate to a boolean field
    campaing_title = models.CharField(max_length=255, blank=True, null=True)
    campaing_short_description = models.TextField(max_length=400,blank=True, null=True)
    campaing_detailed_description = models.TextField(blank=True, null=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    category_type = models.ForeignKey(CategoryType, on_delete=models.CASCADE, related_name='campaigns', null=True, blank=True)
    def __str__(self):
        return self.campaign_name
