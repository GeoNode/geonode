import os
import uuid

from django.db import models
from django.db.models import signals
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.contrib.contenttypes import generic

from geonode.security.models import PermissionLevelMixin
from geonode.security.models import AUTHENTICATED_USERS, ANONYMOUS_USERS
from geonode.layers.models import ResourceBase, Layer
from geonode.people.models import Profile, Role

class ContactRole(models.Model):
    """
    ContactRole is an intermediate model to bind Contacts and Layers and apply roles.
    """
    contact = models.ForeignKey(Profile, related_name='document_contact')
    document = models.ForeignKey('Document', null=True)
    role = models.ForeignKey(Role, related_name='document_role')

    def clean(self):
        """
        Make sure there is only one poc and author per document
        """
        if (self.role == self.document.poc_role) or (self.role == self.document.metadata_author_role):
            contacts = self.ladocumentyer.contacts.filter(contactrole__role=self.role)
            if contacts.count() == 1:
                # only allow this if we are updating the same contact
                if self.contact != contacts.get():
                    raise ValidationError('There can be only one %s for a given document' % self.role)
        if self.contact.user is None:
            # verify that any unbound contact is only associated to one document
            bounds = ContactRole.objects.filter(contact=self.contact).count()
            if bounds > 1:
                raise ValidationError('There can be one and only one document linked to an unbound contact' % self.role)
            elif bounds == 1:
                # verify that if there was one already, it corresponds to this instace
                if ContactRole.objects.filter(contact=self.contact).get().id != self.id:
                    raise ValidationError('There can be one and only one document linked to an unbound contact' % self.role)

    class Meta:
        unique_together = (("contact", "document", "role"),)

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
        
    def _set_poc(self, poc):
        # reset any poc asignation to this document
        ContactRole.objects.filter(role=self.poc_role, document=self).delete()
        #create the new assignation
        ContactRole.objects.create(role=self.poc_role, document=self, contact=poc)

    def _get_poc(self):
        try:
            the_poc = ContactRole.objects.get(role=self.poc_role, document=self).contact
        except ContactRole.DoesNotExist:
            the_poc = None
        return the_poc

    poc = property(_get_poc, _set_poc)

    def _set_metadata_author(self, metadata_author):
        # reset any metadata_author asignation to this document
        ContactRole.objects.filter(role=self.metadata_author_role, document=self).delete()
        #create the new assignation
        ContactRole.objects.create(role=self.metadata_author_role,
                                                  document=self, contact=metadata_author)

    def _get_metadata_author(self):
        try:
            the_ma = ContactRole.objects.get(role=self.metadata_author_role, document=self).contact
        except ContactRole.DoesNotExist:
            the_ma = None
        return the_ma

    metadata_author = property(_get_metadata_author, _set_metadata_author)
        
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

def post_save_document(instance,sender, **kwardg):
    pc, __ = Profile.objects.get_or_create(user=instance.owner,
                                           defaults={"name": instance.owner.username})
    ac, __ = Profile.objects.get_or_create(user=instance.owner,
                                           defaults={"name": instance.owner.username}
                                           )
    instance.poc = pc
    instance.metadata_author = ac

signals.pre_save.connect(pre_save_document, sender=Document)
signals.post_save.connect(post_save_document, sender=Document)