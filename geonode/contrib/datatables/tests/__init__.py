"""
These tests exercise the APIs in the following apps:

    contrib.datatables
    contrib.dataverse_connect
    contrib.dataverse_layer_metadata

Note: All of the imports are independent--e.g. they
may be commented out to run one test import at a time.

Read the comments below.
"""

# LOCAL only tests
# The tests in these 1st two imports run against the LOCAL installation
#
from test_form_jointarget import *
from test_form_upload_and_join import *
from test_name_helper import *

# LOCAL or REMOTE API tests run using the python requests library
#
"""
The tests in the next imports are run against the installation specified in:
    "server_credentials.json" (in this directory)
 If a "server_credentials.json" doesn't exist:
   - Copy "server_credentials_template.json" to "server_credentials.json"
   - Add the necessary url and credentials
"""
from run_test_shapefile_import import *
from run_test_classify_layer import *
from run_test_tabular_api import *
from run_test_lat_lng_api import *
from run_test_dataverse_tabular_api import *

"""
# Run tests from the command line
# cd Documents/github-worldmap/cga-worldmap/geonode; workon cga-worldmap
django-admin.py test datatables --settings=no_db_settings


# For more specific tests, comment out the import lines above as needed

"""
