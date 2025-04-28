#!/bin/bash

export SITEURL=http://localhost:8001/
export BACKEND=geonode.geoserver
export DOCKER_COMPOSE_VERSION=1.19.0
export GEOSERVER_SERVER_URL=http://geoserver:8080/geoserver/
export GEOSERVER_SERVER_PORT=8080
export ON_TRAVIS=True
export TEST_RUNNER_KEEPDB=True
export TEST_RUN_INTEGRATION=True
export TEST_RUN_INTEGRATION_SERVER=False
export TEST_RUN_INTEGRATION_UPLOAD=True
export TEST_RUN_INTEGRATION_MONITORING=False
export TEST_RUN_INTEGRATION_CSW=False
export TEST_RUN_INTEGRATION_BDD=False
export SESSION_EXPIRED_CONTROL_ENABLED=True
export ASYNC_SIGNALS=False
export DATABASE_URL=postgis://geonode:geonode@db:5432/geonode
export GEODATABASE_URL=postgis://geonode:geonode@db:5432/geonode_data
export DEFAULT_BACKEND_DATASTORE=datastore

# echo "Initialize DB";
# chmod +x scripts/misc/create_dbs_travis.sh;
# scripts/misc/create_dbs_travis.sh before_script;

paver run_tests --coverage --local false