from django.db import models

# Create your models here.

class News(models.Model):
    title = models.CharField(max_length=300)
    description = models.TextField()
    image = models.ImageField(null=True, blank=True, upload_to="news_updates")
    publish_date = models.DateTimeField()
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
