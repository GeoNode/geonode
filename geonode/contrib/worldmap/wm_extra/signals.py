from django.db.models.signals import post_save
from django.contrib.auth.models import Group

from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.people.models import Profile


def save_profile(sender, instance, created, **kwargs):
    """
    Add a user to the 'Registered users' group on creation.
    """
    if created:
        group, is_created = Group.objects.get_or_create(name='Registered users')
        group.user_set.add(instance)


def add_ext_layer(sender, instance, created, **kwargs):
    """
    Create an ExtLayer and link it to the created layer.
    """
    if created:
        from .models import ExtLayer
        ExtLayer.objects.create(layer=instance)


def add_ext_map(sender, instance, created, **kwargs):
    """
    Create an ExtMap and link it to the created map.
    """
    if created:
        from .models import ExtMap
        ExtMap.objects.create(map=instance)


post_save.connect(save_profile, sender=Profile)
post_save.connect(add_ext_layer, sender=Layer)
post_save.connect(add_ext_map, sender=Map)
