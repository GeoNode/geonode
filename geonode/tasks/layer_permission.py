from geonode.geoserver.helpers import ogc_server_settings
from datetime import datetime
from django.contrib.auth.models import Group
from guardian.shortcuts import assign_perm, get_anonymous_user
from celery.utils.log import get_task_logger
logger = get_task_logger("geonode.tasks.update")

def fhm_perms_update(layer):
    try:
        # layer.remove_all_permissions()
        anon_group = Group.objects.get(name='anonymous')
        assign_perm('view_resourcebase', anon_group, layer.get_self_resource())
        assign_perm('download_resourcebase', anon_group,
                    layer.get_self_resource())
        assign_perm('view_resourcebase', get_anonymous_user(),
                    layer.get_self_resource())
        assign_perm('download_resourcebase', get_anonymous_user(),
                    layer.get_self_resource())
    except:
        st = str(datetime.now())
        logger.exception(st + " Error in updating style of " + layer.name)
        pass
