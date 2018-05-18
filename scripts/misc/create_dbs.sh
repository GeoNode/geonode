#!/usr/bin/env bash

set -x

BACKEND=geonode.geoserver scripts/misc/create_dbs_travis.sh before_script
