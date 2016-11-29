from geonode.settings import GEONODE_APPS
import geonode.settings as settings
from actstream.models import Action
from geonode.people.models import Profile
from geonode.base.models import ResourceBase


auth_list = Action.objects.filter(verb='downloaded').order_by('timestamp')
for auth in auth_list:
    model_object = DownloadTracker(timestamp=auth.timestamp,
                                actor=str(Profile.objects.get(username=auth.actor)),
                                title=str(auth.action_object.title),
                                resource_type=str(auth.action_object.csw_type),
                                keywords=str(ResourceBase.objects.get(title=auth.action_object.title))
                                )
    model_object.save()
