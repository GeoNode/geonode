#!/usr/bin/env bash

set -x

if [ "$BACKEND" = "geonode.geoserver" ] && [ ! "$TEST_RUN_INTEGRATION_SERVER" = "True" ]; then

	case $1 in
		"before_install")
			echo "Before install scripts"
			ifconfig
			pip install docker-compose==$DOCKER_COMPOSE_VERSION
			scripts/misc/docker_check.sh
			;;
		"before_script")
			echo "Setting up GeoServer Server Backend"
			echo "Start GeoServer Server docker container"
			export GEONODE_PROJECT_PATH=$TRAVIS_BUILD_DIR
			docker-compose -f docker-compose-geoserver-server.yml up -d geoserver
            sleep 30
			docker ps
			docker inspect geoserver4geonode
			echo "Test connection to GeoServer Server"
			wget -qO- $GEOSERVER_SERVER_URL
            wget -qO- ${GEOSERVER_SERVER_URL}ows?service=wms&version=1.3.0&request=GetCapabilities
			;;
		"after_script")
			echo "Shutdown GeoServer Server docker container"
			docker-compose -f docker-compose-geoserver-server.yml down
			;;
	esac
fi
