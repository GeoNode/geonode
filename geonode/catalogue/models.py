import errno
import logging

from django.db.models import signals
from geonode.layers.models import Layer
from geonode.catalogue import get_catalogue


logger = logging.getLogger("geonode.catalogue.models")

def catalogue_pre_delete(instance, sender, **kwargs):
    """Removes the layer from the catalogue
    """
    catalogue = get_catalogue()
    catalogue.remove_record(instance.uuid)



def catalogue_pre_save(instance, sender, **kwargs):
    """Get information from catalogue
    """
    # If the layer is not yet in the database
    # do not attempt to do anything.

    # If it does not have a pk, it has not been saved ...
    if not hasattr(instance, 'pk'):
        return

    # ... but fixtures come with pk's before being saved
    # so we have to check the database
    if not Layer.objects.filter(pk=instance.pk).exists():
        return

    try:
        catalogue = get_catalogue()
        catalogue.create_record(instance)
    except EnvironmentError, e:
        msg = ('Could not connect to catalogue'
               'to save information for layer "%s"' % (instance.name)
              )
        if e.reason.errno == errno.ECONNREFUSED:
            logger.warn(msg, e) 
        else:
            raise e


def catalogue_post_save(instance, sender, **kwargs):
    """Send information to catalogue
    """
    meta = None
    try:
        catalogue = get_catalogue()
        meta = catalogue.get_record(instance.uuid)
    except EnvironmentError, e:
        msg = ('Could not connect to catalogue'
               'to save information for layer "%s"' % (instance.name)
              )
        if e.reason.errno == errno.ECONNREFUSED:
            logger.warn(msg, e)
        else:
            raise e

    if meta is None:
        return

    if hasattr(meta.distribution, 'online'):
        onlineresources = [r for r in meta.distribution.online if r.protocol == "WWW:LINK-1.0-http--link"]
        if len(onlineresources) == 1:
            res = onlineresources[0]
            instance.distribution_url = res.url
            instance.distribution_description = res.description
    #FIXME(Ariel): Is there a commit of some sort needed here for it to be saved in the catalogue?

signals.pre_save.connect(catalogue_pre_save, sender=Layer)
signals.post_save.connect(catalogue_post_save, sender=Layer)
signals.pre_delete.connect(catalogue_pre_delete, sender=Layer)
