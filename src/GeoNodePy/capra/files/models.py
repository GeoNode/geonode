from os import path
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.db import models

fs = FileSystemStorage(location=settings.GEONODE_UPLOAD_PATH)

class AMEFile(models.Model):
    file = models.FileField(storage=fs, upload_to='ame')
    title = models.CharField(max_length=255, blank=True, help_text="If blank, the filename is used.")
    scenario = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    
    @property
    def name(self):
        return self.title or self.filename
    
    @property
    def download_url(self):
        return self.file.url

    @property
    def filename(self):
        return path.split(self.file.name)[1]