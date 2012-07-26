import errno
import logging

from django.db.models import signals
from geonode.layers.models import Layer, Link
from geonode.catalogue import get_catalogue


logger = logging.getLogger(__name__)

def catalogue_pre_delete(instance, sender, **kwargs):
    """Removes the layer from the catalogue
    """
    catalogue = get_catalogue()
    catalogue.remove_record(instance.uuid)



def catalogue_post_save(instance, sender, **kwargs):
    """Get information from catalogue
    """
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


def catalogue_pre_save(instance, sender, **kwargs):
    """Send information to catalogue
    """
    # If the layer is not yet in the database
    # do not attempt to do anything.
    import pdb;pdb.set_trace()

    # If it does not have a pk, it has not been saved ...
    if not hasattr(instance, 'pk'):
        return

    # ... but fixtures come with pk's before being saved
    # so we have to check the database
    if not Layer.objects.filter(pk=instance.pk).exists():
        return


    record = None
    try:
        catalogue = get_catalogue()
        record = catalogue.get_record(instance.uuid)
    except EnvironmentError, e:
        msg = ('Could not connect to catalogue'
               'to save information for layer "%s"' % (instance.name)
              )
        if e.reason.errno == errno.ECONNREFUSED:
            logger.warn(msg, e)
        else:
            raise e

    if record is None:
        return

    # Fill in the url for the catalogue
    if hasattr(record.distribution, 'online'):
        onlineresources = [r for r in record.distribution.online if r.protocol == "WWW:LINK-1.0-http--link"]
        if len(onlineresources) == 1:
            res = onlineresources[0]
            instance.distribution_url = res.url
            instance.distribution_description = res.description

    # Create the different metadata links with the available formats
    for link in record.links['metadata']:
        instance.link_set.objects.create(
                           layer=instance,
                           name=link[0],
                           extension='xml',
                           mime=link[1],
                           url=link[2],
                           link_type='metadata',
                           )

signals.pre_save.connect(catalogue_pre_save, sender=Layer)
signals.post_save.connect(catalogue_post_save, sender=Layer)
signals.pre_delete.connect(catalogue_pre_delete, sender=Layer)
