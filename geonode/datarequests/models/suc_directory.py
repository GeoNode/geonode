from django.db import models
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.utils import dateformat
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext as _
from django.utils.encoding import iri_to_uri
from django.utils.http import urlquote
from django_enumfield import enum
from django.core import validators

class SUC_Contact(models.Model):
    institution_abrv = models.CharField(_('Institution Name(abbrev.)'), max_length=50, null=False, blank = False )
    institution_full = models.CharField(_('Institution Name(full)'), max_length=100, null=False, blank = False )
    name = models.CharField(_('Full name of contact person'),max_length = 100)
    position = models.CharField(_('Position'),max_length = 50)
    email_address = models.EmailField(_('Email Address'))
    salutation = models.CharField(_('Salutation (optional)'), max_length = 10, blank=True, null = True)
    username = models.CharField(_('Username associated with this SUC contact'), max_length=50, null=False, blank=False)   
    
    class Meta:
        app_label = "datarequests"
        verbose_name = "SUC Contact"
    
    def __unicode__(self):
        s = ""
        
        if self.salutation:
            s += self.salutation
            
        s += "{0}, {1} for {2}".format(self.name, self.position, self.institution_full)
        
        return s
    
