import logging
import os
import sys
import uuid

from django.db import models
from django.db.models import signals
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.contrib.contenttypes import generic
from django.conf import settings

from geonode.security.enumerations import AUTHENTICATED_USERS, ANONYMOUS_USERS
from geonode.layers.models import Layer
from geonode.base.models import ResourceBase, resourcebase_post_save
from geonode.maps.signals import map_changed_signal
from geonode.maps.models import Map

IMGTYPES = ['jpg', 'jpeg', 'tif', 'tiff', 'png', 'gif']

logger = logging.getLogger(__name__)

class Document(ResourceBase):
    """
    A document is any kind of information that can be attached to a map such as pdf, images, videos, xls...
    """

    # Relation to the resource model
    content_type = models.ForeignKey(ContentType, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    resource = generic.GenericForeignKey('content_type', 'object_id')

    doc_file = models.FileField(upload_to='documents')
    extension = models.CharField(max_length=128, blank=True, null=True)

    popular_count = models.IntegerField(default=0)
    share_count = models.IntegerField(default=0)

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
        current_perms = self.get_all_level_info()
        for username in current_perms['users'].keys():
            user = User.objects.get(username=username)
            self.set_user_level(user, self.LEVEL_NONE)
        
        # assign owner admin privileges
        if self.owner:
            self.set_user_level(self.owner, self.LEVEL_ADMIN)

    def update_thumbnail(self, save=True):
        try:
            self.save_thumbnail(None, save)
        except RuntimeError, e:
            logger.warn('Could not create thumbnail for %s' % self, e)

    def _render_thumbnail(self, spec):
        size = 200, 150
        try:
            from cStringIO import StringIO
            from PIL import Image, ImageOps
            if self.extension.lower() in IMGTYPES:
                img = Image.open(self.doc_file.path)
                img = ImageOps.fit(img, size, Image.ANTIALIAS)

            elif self.extension.lower() == 'pdf':
                try:
                    # if wand is installed, than use it for pdf thumbnailing
                    from wand import image

                    logger.debug('Generating a thumbnail for document: {0}'.format(self.title))
                    with image.Image(filename=self.doc_file.path) as img:
                        img.sample(*size)
                        return img.make_blob('png')
                except:
                    logger.debug('Wand not installed or invalid file, use the generic pdf placeholder.')
                    img = Image.open('%s/documents/static/documents/%s' %
                        (settings.PROJECT_ROOT, '{0}-placeholder.png'.format(self.extension)))
            else:
                filename = '%s-placeholder.png' % self.extension
                try:
                    img = Image.open('%s/documents/static/documents/%s' %
                        (settings.PROJECT_ROOT, filename))
                except IOError:
                    img = Image.open(
                        '%s/documents/static/documents/generic-placeholder.png' %
                        settings.PROJECT_ROOT)
            imgfile = StringIO()
            img.save(imgfile, format='PNG')
            return imgfile.getvalue()
        except:
            logger.error('Pillow not installed, cannot generate thumbnails.')
            return None

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
    
    if not instance.uuid:
        instance.uuid = str(uuid.uuid1())
    instance.csw_type = 'document'
    
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
    else:
        instance.bbox_x0 = -180
        instance.bbox_x1 = 180
        instance.bbox_y0 = -90
        instance.bbox_y1 = 90


def create_thumbnail(sender, instance, created, **kwargs):
    if created:
        instance.update_thumbnail(save=False)


def update_documents_extent(sender, **kwargs):
    model = 'map' if isinstance(sender, Map) else 'layer'
    ctype = ContentType.objects.get(model= model)
    for document in Document.objects.filter(content_type=ctype, object_id=sender.id):
        document.save()

signals.pre_save.connect(pre_save_document, sender=Document)
signals.post_save.connect(create_thumbnail, sender=Document)
signals.post_save.connect(resourcebase_post_save, sender=Document)
map_changed_signal.connect(update_documents_extent)
