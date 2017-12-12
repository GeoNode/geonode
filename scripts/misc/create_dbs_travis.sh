#!/usr/bin/env bash

set -x

if [ "$BACKEND" = "geonode.geoserver" ]; then

	case $1 in
		"before_install")
			echo "Before install scripts"
			;;
		"before_script")
			echo "Setting up PostGIS Backend"
			export GEONODE_PROJECT_PATH=$TRAVIS_BUILD_DIR
      sudo -u postgres dropdb template_postgis
      sudo -u postgres dropdb geonode
      sudo -u postgres dropdb geonode_data
      sudo -u postgres dropdb upload_test
      sudo -u postgres dropuser geonode
      sudo -u postgres createuser geonode -d
      sudo -u postgres createdb template_postgis
      sudo -u postgres psql -d template_postgis -c 'CREATE EXTENSION postgis;'
      sudo -u postgres psql -d template_postgis -c 'GRANT ALL ON geometry_columns TO PUBLIC;'
      sudo -u postgres psql -d template_postgis -c 'GRANT ALL ON spatial_ref_sys TO PUBLIC;'
      sudo -u postgres createdb -O geonode geonode
      sudo -u postgres createdb -T template_postgis -O geonode geonode_data
      sudo -u postgres createdb -T template_postgis -O geonode upload_test
			;;
		"after_script")
			;;
	esac
fi
