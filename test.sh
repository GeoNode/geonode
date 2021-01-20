#!/bin/bash
set -e
. $HOME/.override_env

coverage run --branch --source=geonode manage.py test -v 3 --keepdb  $@