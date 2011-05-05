#!/bin/bash

GEONODE_URL="http://localhost:8000/"
GEOSERVER_URL="http://localhost:8001/geoserver/"

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
source ../geonode/bin/activate

# Make sure GeoNode and GeoServer are running

gn=$(curl --write-out %{http_code} --silent --output /dev/null ${GEONODE_URL})

if [ $gn != "200" ]; then
    echo ">>> GeoNode is not Running. Please Start it"
    exit 1
fi

gs=$(curl --write-out %{http_code} --silent --output /dev/null ${GEOSERVER_URL})
if [ $gs != "200" ]; then
    echo ">>> GeoServer is not Running"
    exit 1
fi

# Run the tests
echo ">>>> Running GeoNode Integration Tests" 
python manage.py test
