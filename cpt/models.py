from django.db import models
from django.core.validators import RegexValidator
from django.utils.text import slugify
import uuid
from django.utils import timezone


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


        # form_enabled= True {allow_drawings,categories,"create from in frontend"}
        # if form_enabled  false, allow drawing e izin vermycez.
        #rate_enabled defautl true olacak

class Campaign(models.Model):
    campaign_id = models.AutoField(primary_key=True)  # Auto-generated ID
    campaign_name = models.CharField(max_length=255, null=False, blank=False,)
    campaign_url_name = models.SlugField(max_length=30, unique=True, validators=[
        RegexValidator(regex=r'^[a-z0-9\-_]+$', message='Only lowercase letters, numbers, hyphens, and underscores allowed.')
    ], null=True, blank=True)
    campaing_title = models.CharField(max_length=255, blank=False, null=False, )
    campaing_short_description = models.CharField(max_length=255, blank=False, null=False,)
    campaing_detailed_description = models.TextField(blank=False, null=False, )
    start_date = models.DateTimeField(blank=False, null=False,default=timezone.now())
    end_date = models.DateTimeField(blank=False, null=False)
    rate_enabled = models.BooleanField(default=True, null=True, blank=True)  # Set default to True
    form_enabled = models.BooleanField(default=False, null=True, blank=True) 
    allow_drawings = models.BooleanField(default=False, null=True)
    category_type = models.ForeignKey(CategoryType, on_delete=models.CASCADE, related_name='campaigns', null=True, blank=True)
    geoserver_workspace = models.CharField(max_length=100, blank=True, null=True)  
    
    
# 
    def save(self, *args, **kwargs):
        if not self.campaign_url_name:
            self.campaign_url_name = slugify(self.campaign_name) or str(uuid.uuid4())
        if not self.form_enabled:
            self.allow_drawings = False
        if not self.form_enabled:
            self.category_type=None
        super(Campaign, self).save(*args, **kwargs)

    def __str__(self):
        return self.campaign_name


class Rating(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='ratings')
    rating = models.IntegerField()
    form = models.ForeignKey('Form', on_delete=models.SET_NULL, null=True, blank=True, related_name='ratings')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Rating {self.rating} for Campaign {self.campaign.campaign_name}'


from django.db import models
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.db import models as gis_models

class Form(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='forms')
    feedback_location = gis_models.PointField()  # Store as a PostGIS Point
    feedback_text = models.TextField()
    feedback_category = models.CharField(max_length=100)
    feedback_geometry = models.TextField(null=True, blank=True)  # Store GeoJSON as raw string
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Feedback for Campaign {self.campaign.campaign_name}'

    def save(self, *args, **kwargs):
        # Convert feedback_location from GeoJSON to Point if it's provided as a string
        if isinstance(self.feedback_location, str):
            self.feedback_location = GEOSGeometry(self.feedback_location)
        super().save(*args, **kwargs)