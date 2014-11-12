from hashlib import md5, sha224

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.db import models

from datetime import date, datetime

from django.utils.timezone import utc
from django.contrib.auth.models import User

from geonode.maps.models import Layer
from geonode.dataverse_layer_metadata.models import DataverseLayerMetadata

import urllib




class RegisteredApplication(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(help_text='contact info, etc')
    contact_email = models.EmailField()
    
    hostname = models.CharField(max_length=255, blank=True)
    ip_address = models.CharField(max_length=15, blank=True)
    
    #mapit_link = models.URLField(help_text='http://geoconnect.harvard.edu')
    #api_permissions = models.ManyToManyField(APIPermission, blank=True, null=True)
    
    time_limit_minutes = models.IntegerField(default=30, help_text='in minutes')
    time_limit_seconds = models.IntegerField(default=0, help_text='autofilled on save')
    
    md5 = models.CharField(max_length=40, blank=True, db_index=True, help_text='auto-filled on save')
    
    update_time = models.DateTimeField(auto_now=True)
    create_time = models.DateTimeField(auto_now_add=True)
    
    def __unicode__(self):
        return self.name
        
    def save(self, *args, **kwargs):
        if not self.id:
            super(RegisteredApplication, self).save(*args, **kwargs)
        
        self.md5 = md5('%s%s' % (self.id, self.name)).hexdigest()
        self.time_limit_seconds = self.time_limit_minutes * 60  
        super(RegisteredApplication, self).save(*args, **kwargs)


    class Meta:
        verbose_name = 'Application information'
        verbose_name_plural = verbose_name


class WorldMapToken(models.Model):
    """
    Appended to a URL for viewing a private layer
    """
    token = models.CharField(max_length=255, blank=True, help_text = 'auto-filled on save', db_index=True)
    application = models.ForeignKey(RegisteredApplication)

    dataverse_metadata_info = models.ForeignKey(DataverseLayerMetadata)
    map_layer = models.ForeignKey(Layer)
    
    has_expired = models.BooleanField(default=False)
    
    last_refresh_time =  models.DateTimeField(auto_now_add=True)
           
    update_time = models.DateTimeField(auto_now=True)
    create_time = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '%s (%s)' % (self.map_layer, self.dataverse_metadata_info)


    def has_token_expired(self, current_time=None):
        """Check if the token has expired.
        Find the difference between the current time and the token's "last_refresh_time"
        Compare it to the RegisteredApplication "time_limit_seconds" attribute
        
        :current_time   datetime object that is timezone aware or None
        """
        if current_time is None:
            current_time = datetime.now()    #.replace(tzinfo=utc)
        
        try:
            mod_time = current_time - self.last_refresh_time
        except:
            return True
        
        if mod_time.seconds > self.application.time_limit_seconds:
            self.has_expired = True
            self.save()
            return True
        
        return False
        
        
    def refresh_token(self):
        current_time = datetime.utcnow().replace(tzinfo=utc)
        if self.has_token_expired(current_time):
            return False            
        self.last_refresh_time = current_time
        self.save()
        return True
        
    def save(self, *args, **kwargs):
        if not self.id:
            super(WorldMapToken, self).save(*args, **kwargs)
        
        if not self.token:
            self.token = sha224('[id:%s][sf:%s]' % (self.id, self.map_layer.id )).hexdigest()

        super(WorldMapToken, self).save(*args, **kwargs)
    
    def get_view_layer_with_token(self, request):
        #metadata_url = reverse('view_data_file_metadata', kwargs={'dv_token' : self.token})
        
        d = {}
        metadata_url = reverse('view_data_file_metadata_base_url', kwargs={})
        d['cb'] = request.build_absolute_uri(metadata_url) #request.get_host()
        callback_url = urllib.urlencode(d)
        return self.application.mapit_link + '%s/?%s' % (self.token, callback_url)
    
    def file_metadata(self):
        lnk = reverse('view_data_file_metadata', kwargs={ 'dv_token' : self.token })
        return '<a href="%s">metadata api</a>' % lnk
    file_metadata.allow_tags = True
    
    @staticmethod
    def get_new_token(registered_application, dataverse_metadata_info, map_layer):
        assert type(registered_application) is RegisteredApplication, "registered_application must be a RegisteredApplication object"
        assert type(dataverse_metadata_info) is DataverseLayerMetadata, "dataverse_metadata_info must be a DataverseLayerMetadata object"
        assert type(map_layer) is Layer, "map_layer must be a Layer object"
       

        worldmap_token = WorldMapToken(application=registered_application\
                                , dataverse_metadata_info=dataverse_metadata_info\
                                , map_layer=map_layer\
                                )
        worldmap_token.save()
        
        return worldmap_token