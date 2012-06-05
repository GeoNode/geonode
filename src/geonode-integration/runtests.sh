#!/bin/bash

GEONODE_URL="http://localhost/"
GEOSERVER_URL="http://localhost:8001/geoserver-geonode-dev/"

if [ ! -d "./geonode_test_data" ]; then
    echo ">>>> Downloading Test Data"
    wget "http://dev.geonode.org/test-data/geonode_test_data.tgz"
    tar xvzf geonode_test_data.tgz
    rm geonode_test_data.tgz
fi

# Activate the virtualenv
# How can we test if its already activated?
# Assumes that geonode and geonode_tests are next to each other
echo ">>>> Activating VirtualEnv"
source ../../bin/activate

# Run the tests
echo ">>>> Running GeoNode Integration Tests" 
python manage.py test "$@"
