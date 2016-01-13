from django.db import models
from django_enumfield import enum

# Create your models here.
class SRS(enum.Enum):
    UTM51 = 32651
    PRS92 = 4683
    
    labels = {
        UTM51: 'UTM 51 (Default)',
        PRS92: 'PRS 92',}