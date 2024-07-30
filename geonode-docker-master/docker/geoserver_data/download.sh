#!/usr/bin/env sh

# Wait for version to come up before downloading it
# args  $1 - version
# args  $2 - temp directory

echo "GeoServer Data Dir version is $1"
echo "-----------------------------------------------------------------------------------------------"
echo "Archive temporary directory is $2"

GEOSERVER_VERSION=$1
TEMP_DOWNLOADED=$2 

echo "GeoServer Data Directory is going to be downloaded"
artifact_url="https://artifacts.geonode.org/geoserver/$GEOSERVER_VERSION/geonode-geoserver-ext-web-app-data.zip"
echo "Downloading: $artifact_url"
curl  -k -L "$artifact_url" --output data.zip && unzip -x -d ${TEMP_DOWNLOADED} data.zip
echo "GeoServer Data Directory download has been completed"
