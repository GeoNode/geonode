import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


##### USER TO USE FOR AUTHENTICATION WITH CEPH
CEPH_USER = 'geonode:swift'

##### KEY ASSOCIATED WITH CEPH_USER FOR AUTHENTICATION
CEPH_KEY = 'Ry3meRcVwVkff3G2O1vSy0PmUvUcXCzvWNZic04B'

##### CEPH CLIENT URL
CEPH_URL = 'https://cephclient.lan.dream.upd.edu.ph'
#CEPH_URL = "http://cephclient.phil-lidar1.tld"

##### DEFAULT STORAGE CONTAINER
DEFAULT_CONTAINER = 'test-container'
# DEFAULT_CONTAINER = 'geo-container'
