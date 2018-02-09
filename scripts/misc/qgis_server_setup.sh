#!/usr/bin/env bash

set -x

if [ "$BACKEND" = "geonode.qgis_server" ]; then

	case $1 in
		"before_install")
			echo "Before install scripts"
			ifconfig
			pip install docker-compose==$DOCKER_COMPOSE_VERSION
			scripts/misc/docker_check.sh
			;;
		"before_script")
			echo "Setting up QGIS Server Backend"
			echo "Start QGIS Server docker container"
			export GEONODE_PROJECT_PATH=$TRAVIS_BUILD_DIR
			docker-compose -f docker-compose-qgis-server.yml up -d qgis-server
			docker ps
			docker inspect geonode_qgis-server_1
			echo "Test connection to QGIS Server"
			wget -qO- $QGIS_SERVER_URL
			wget -qO- ${QGIS_SERVER_URL}?SERVICE=MAPCOMPOSITION
			echo "Copy QGIS Server configuration"
			cp geonode/local_settings.py.qgis.sample geonode/local_settings.py
			;;
		"after_script")
			echo "Shutdown QGIS Server docker container"
			docker-compose -f docker-compose-qgis-server.yml down
			echo "Remove settings file"
			rm geonode/local_settings.py
			;;
	esac
fi
