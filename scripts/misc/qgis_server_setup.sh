#!/usr/bin/env bash

set -x

if [ $BACKEND = "geonode.qgis_server" ] && [ $1 = "before_install" ]; then
	echo "Before install scripts"
	ifconfig
	docker --version
	pip install docker-compose==$DOCKER_COMPOSE_VERSION
	docker-compose --version
	docker pull kartoza/qgis-server:LTR
fi

if [ $BACKEND = "geonode.qgis_server" ] && [ $1 = "before_script" ]; then
	echo "Setting up QGIS Server Backend"
	echo "Clone OTF Project Plugin"
	git clone https://github.com/kartoza/otf-project.git
	cd otf-project
	git checkout master
	cd ../
	echo "Start QGIS Server docker container"
	docker-compose -f docker-compose-qgis-server.yml up -d qgis-server
	docker ps
	echo "Copy QGIS Server configuration"
	cp geonode/local_settings.py.qgis.sample geonode/local_settings.py
fi

if [ $BACKEND = "geonode.qgis_server" ] && [ $1 = "after_script" ]; then
	echo "Shutdown QGIS Server docker container"
	docker-compose -f docker-compose-qgis-server.yml down
	echo "Remove settings file"
	rm geonode/local_settings.py
fi
