import os
import uuid

from django.db import models
from django.db.models import signals
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.contrib.contenttypes import generic

from geonode.security.enumerations import AUTHENTICATED_USERS, ANONYMOUS_USERS
from geonode.layers.models import Layer
from geonode.base.models import TopicCategory, ResourceBase
from geonode.maps.signals import map_changed_signal
from geonode.maps.models import Map
from geonode.utils import bbox_to_wkt
from geonode.people.models import Profile, Role

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

def pre_save_document(instance, sender, **kwargs):
    base_name, extension = os.path.splitext(instance.doc_file.name)
    instance.extension=extension[1:]
    
    instance.uuid = str(uuid.uuid1())
    
    if instance.abstract == '' or instance.abstract is None:
        instance.abstract = 'No abstract provided'

    if instance.title == '' or instance.title is None:
        instance.title = instance.name

    if instance.poc is None:
        instance.contactrole_set.create(role=instance.poc_role,
                                         contact=Layer.objects.admin_contact())

    if instance.metadata_author is None:
        instance.contactrole_set.create(role=instance.metadata_author_role,
                                         contact=Layer.objects.admin_contact())
    if instance.resource:
        instance.csw_wkt_geometry = instance.resource.geographic_bounding_box
        instance.bbox_x0 = instance.resource.bbox_x0
        instance.bbox_x1 = instance.resource.bbox_x1
        instance.bbox_y0 = instance.resource.bbox_y0
        instance.bbox_y1 = instance.resource.bbox_y1

def post_save_document(instance,sender, **kwargs):
    pc, __ = Profile.objects.get_or_create(user=instance.owner,
                                           defaults={"name": instance.owner.username})
    ac, __ = Profile.objects.get_or_create(user=instance.owner,
                                           defaults={"name": instance.owner.username}
                                           )
    instance.poc = pc
    instance.metadata_author = ac

def update_documents_extent(sender, **kwargs):
    model = 'map' if isinstance(sender, Map) else 'layer'
    ctype = ContentType.objects.get(model= model)
    for document in Document.objects.filter(content_type=ctype, object_id=sender.id):
        document.save()

signals.pre_save.connect(pre_save_document, sender=Document)
signals.post_save.connect(post_save_document, sender=Document)
map_changed_signal.connect(update_documents_extent)