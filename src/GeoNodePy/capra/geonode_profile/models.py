from django.db import models
from geonode.maps.forms import COUNTRIES
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.ForeignKey(User)
    name = models.CharField('Individual Name', max_length=255)
    organization = models.CharField('Organization Name', max_length=255, blank=True, null=True)
    position = models.CharField('Position Name', max_length=255, blank=True, null=True)
    voice = models.CharField('Voice', max_length=255, blank=True, null=True)
    fax = models.CharField('Facsimile',  max_length=255, blank=True, null=True)
    delivery = models.CharField('Delivery Point', max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    area = models.CharField('Administrative Area', max_length=255, blank=True, null=True)
    zipcode = models.CharField('Postal Code', max_length=255, blank=True, null=True)
    country = models.CharField(choices=COUNTRIES, max_length=3, blank=True, null=True)

    
    def get_absolute_url(self):
        return ('profiles_profile_detail', (), { 'username': self.user.username })
    get_absolute_url = models.permalink(get_absolute_url)
    
    def __unicode__(self):
        return self.name