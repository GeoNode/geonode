from django.db import models
from django.utils.translation import ugettext_lazy as _


class Database(models.Model):
    """
    A model representing a database shard.
    """
    YEARLY = 0
    MONTHLY = 1
    LAYERCOUNT = 2
    SHARD_STRATEGY_TYPE = (
        (YEARLY, 'yearly'),
        (MONTHLY, 'monthly'),
        (LAYERCOUNT, 'layercount'),
    )

    name = models.TextField(_("Database Shard Name"))
    layers_count = models.IntegerField(_("Layers Count"), default=0)
    created_at = models.DateTimeField(auto_now=True)
    strategy_type = models.IntegerField(choices=SHARD_STRATEGY_TYPE)

    class Meta:
        verbose_name_plural = 'Shard Databases'
