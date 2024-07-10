#!/bin/bash
# USAGE: ./download_plugins.sh GEOSERVER_VERSION PLUGINS
# EXAMPLE: ./download_plugins.sh "2.23.0 "vectortiles netcdf"
GEOSERVER_VERSION=$1
PLUGINS=$2

echo "GEOSERVER_VERSION: $GEOSERVER_VERSION"
echo "PLUGINS: $PLUGINS"

# clean plugins folder
echo "clean up old plugins in ./plugins/"
mkdir -p ./plugins
find ./plugins ! -name '.keep' -type f -exec rm -f {} +

for plugin in $PLUGINS; do \
  echo "fetching data for $plugin"
  wget https://downloads.sourceforge.net/project/geoserver/GeoServer/$GEOSERVER_VERSION/extensions/geoserver-$GEOSERVER_VERSION-$plugin-plugin.zip && \
  unzip -o geoserver-$GEOSERVER_VERSION-$plugin-plugin.zip -d ./plugins && \
  rm geoserver-$GEOSERVER_VERSION-$plugin-plugin.zip; \
done
printf "......\n\nfinished downloading plugins\n"