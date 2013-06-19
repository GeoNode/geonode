import os
import uuid

from django.db import models
from django.db.models import signals
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.contrib.contenttypes import generic

from geonode.security.enumerations import AUTHENTICATED_USERS, ANONYMOUS_USERS
from geonode.layers.models import Layer
from geonode.base.models import ResourceBase, resourcebase_post_save, \
     resourcebase_post_delete
from geonode.maps.signals import map_changed_signal
from geonode.maps.models import Map
from geonode.people.models import Profile

class Document(ResourceBase):
    """

    A document is any kind of information that can be attached to a map such as pdf, images, videos, xls...

    """

    # Relation to the resource model
    content_type = models.ForeignKey(ContentType,blank=True,null=True)
    object_id = models.PositiveIntegerField(blank=True,null=True)
    resource = generic.GenericForeignKey('content_type', 'object_id')

    doc_file = models.FileField(upload_to='documents')
    extension = models.CharField(max_length=128,blank=True,null=True)

    def __unicode__(self):  
        return self.title
        
    def get_absolute_url(self):
        return reverse('document_detail', args=(self.id,))
        
    class Meta:
        # custom permissions,
        # change and delete are standard in django
        permissions = (
            ('view_document', 'Can view'), 
            ('change_document_permissions', "Can change permissions"),
        )

    LEVEL_READ  = 'document_readonly'
    LEVEL_WRITE = 'document_readwrite'
    LEVEL_ADMIN = 'document_admin'
    
    def set_default_permissions(self):
        self.set_gen_level(ANONYMOUS_USERS, self.LEVEL_READ)
        self.set_gen_level(AUTHENTICATED_USERS, self.LEVEL_READ)
        
        # remove specific user permissions
        current_perms =  self.get_all_level_info()
        for username in current_perms['users'].keys():
            user = User.objects.get(username=username)
            self.set_user_level(user, self.LEVEL_NONE)
        
        # assign owner admin privs
        if self.owner:
            self.set_user_level(self.owner, self.LEVEL_ADMIN)

    @property
    def class_name(self):
        return self.__class__.__name__

def get_related_documents(resource):
    if isinstance(resource, Layer) or isinstance(resource, Map):
        ct = ContentType.objects.get_for_model(resource)
        return Document.objects.filter(content_type=ct,object_id=resource.pk)
    else: return None

def pre_save_document(instance, sender, **kwargs):
    base_name, extension = os.path.splitext(instance.doc_file.name)
    instance.extension=extension[1:]
    
    instance.uuid = str(uuid.uuid1())
    
    if instance.abstract == '' or instance.abstract is None:
        instance.abstract = 'No abstract provided'

    if instance.title == '' or instance.title is None:
        instance.title = instance.name

    if instance.resource:
        instance.csw_wkt_geometry = instance.resource.geographic_bounding_box.split(';')[-1]
        instance.bbox_x0 = instance.resource.bbox_x0
        instance.bbox_x1 = instance.resource.bbox_x1
        instance.bbox_y0 = instance.resource.bbox_y0
        instance.bbox_y1 = instance.resource.bbox_y1

def update_documents_extent(sender, **kwargs):
    model = 'map' if isinstance(sender, Map) else 'layer'
    ctype = ContentType.objects.get(model= model)
    for document in Document.objects.filter(content_type=ctype, object_id=sender.id):
        document.save()

signals.pre_save.connect(pre_save_document, sender=Document)
signals.post_save.connect(resourcebase_post_save, sender=Document)
signals.post_delete.connect(resourcebase_post_delete, sender=Document)
map_changed_signal.connect(update_documents_extent)
