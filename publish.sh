#!/bin/bash
source ~/Envs/geonode/bin/activate
pushd $(dirname $0)
DJANGO_SETTINGS_MODULE=geonode.settings paver publish
exit 0
