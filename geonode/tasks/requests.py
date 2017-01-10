import sys
import traceback
from pprint import pprint
from celery.task import task

import geonode.settings as settings
from geonode.datarequests.models import (
    ProfileRequest, DataRequest, DataRequestProfile)

@task(name="geonode.tasks.requests.set_status_for_multiple_requests",queue='requests')
def set_status_for_multiple_requests(requests, status, administrator=None):
    for r in requests:
        r.set_status(status, administrator)
    
