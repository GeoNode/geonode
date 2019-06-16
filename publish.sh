#!/bin/bash
# source ~/.virtualenvs/geonode/bin/activate
pushd $(dirname $0)
DJANGO_SETTINGS_MODULE=geonode.settings PPA_GEONODE=geonode/testing paver publish
exit 0
