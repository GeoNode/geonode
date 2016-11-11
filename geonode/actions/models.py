from django.db import models

try:
    from django.utils import timezone
    now = timezone.now
except ImportError:
    from datetime import datetime
    now = datetime.now


ACTION_TYPES = [
    ['layer_delete', 'Layer Deleted'],
    ['layer_create', 'Layer Created'],
    ['layer_upload', 'Layer Uploaded'],
    ['map_delete', 'Map Deleted'],
    ['map_create', 'Map Created'],
]

class Action(models.Model):
    """
    Model to store user actions, such a layer creation or deletion.
    """
    action_type = models.CharField(max_length=25, choices=ACTION_TYPES)
    description = models.CharField(max_length=255, db_index=True)
    args = models.CharField(max_length=255, db_index=True)
    timestamp = models.DateTimeField(default=now, db_index=True)
