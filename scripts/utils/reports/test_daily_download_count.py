from geonode.settings import GEONODE_APPS
import geonode.settings as settings
from actstream.models import Action
from geonode.eula.models import AnonDownloader
from geonode.reports.models import DownloadCount, SUCLuzViMin, DownloadTracker
from datetime import datetime, timedelta
from geonode.layers.models import Layer
from geonode.cephgeo.models import FTPRequest, FTPRequestToObjectIndex, DataClassification
from geonode.people.models import Profile
from daily_download_count import *

import sys

timedeltadays = int(sys.argv[1])

main(timedeltadays,DownloadTracker.objects, 'timestamp', 'actor','resource_type','title', False)
main(timedeltadays,AnonDownloader.objects, 'date', False,'anon_document','anon_layer', False)
main(timedeltadays,FTPRequest.objects,'date_time','user','','',True)
print(layer_count)

# save_to_dc(timedeltadays,layer_count)
