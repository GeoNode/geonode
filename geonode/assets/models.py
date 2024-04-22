from django.db import models
from django.utils.timezone import now
from polymorphic.managers import PolymorphicManager
from polymorphic.models import PolymorphicModel
from django.db.models import signals
from django.contrib.auth import get_user_model


class Asset(PolymorphicModel):
    """
    A generic data linked to a ResourceBase
    """

    title = models.CharField(max_length=255, null=False, blank=False)
    description = models.TextField(null=True, blank=True)
    type = models.CharField(max_length=255, null=False, blank=False)
    owner = models.ForeignKey(get_user_model(), null=False, blank=False, on_delete=models.CASCADE)
    created = models.DateTimeField(default=now)

    objects = PolymorphicManager()

    class Meta:
        verbose_name_plural = "Assets"

    def __str__(self) -> str:
        return super().__str__()


class LocalAsset(Asset):
    """
    Local resource, will replace the files
    """

    location = models.JSONField(default=list, blank=True)

    class Meta:
        verbose_name_plural = "Local assets"

    def __str__(self) -> str:
        return super().__str__()


def cleanup_asset_data(instance, *args, **kwargs):
    from geonode.assets.handlers import asset_handler_registry

    asset_handler_registry.get_handler(instance).remove_data(instance)


signals.post_delete.connect(cleanup_asset_data, sender=LocalAsset)
