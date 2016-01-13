from django.db import models
from django_enumfield import enum

# Create your models here.
class SRS(enum.Enum):
    UTM51N = 32651
    PRS92 = 4683
    
    labels = {
        UTM51N: 'UTM 51N (Default)',
        PRS92: 'PRS 92',}