from geonode.settings import GEONODE_APPS
import geonode.settings as settings
from actstream.models import Action
from geonode.people.models import Profile
from geonode.base.models import ResourceBase
from geonode.reports.models import DownloadTracker


auth_list = Action.objects.filter(verb='downloaded').order_by('timestamp')
for auth in auth_list:
    try:
        model_object = DownloadTracker.objects.get(timestamp=auth.timestamp,
                                actor=Profile.objects.get(username=auth.actor),
                                title=str(auth.action_object.title),
                                resource_type=str(auth.action_object.csw_type),
                                keywords=str(ResourceBase.objects.filter(title=auth.action_object.title)[0].keywords.slugs()),
                                dl_type=""
                                )
        print ('it already exists')
    except:
        model_object = DownloadTracker(timestamp=auth.timestamp,
                                actor=Profile.objects.get(username=auth.actor),
                                title=str(auth.action_object.title),
                                resource_type=str(auth.action_object.csw_type),
                                keywords=str(ResourceBase.objects.filter(title=auth.action_object.title)[0].keywords.slugs()),
                                dl_type=""
                                )
        model_object.save()
        print ('saved')
