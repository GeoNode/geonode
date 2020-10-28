#!/bin/bash
set -e

coverage run --branch --source=geonode manage.py test $@
