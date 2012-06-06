GeoNode Integration Test Suite

To download the test data and run the test suite, use the following command

    export GEONODE_HOME=../geonode/
    ./runtests.sh

The above assumes that a working checkout/build of geonode is located next to i
this repo on the filesystem and that GeoNode has been started in the default 
way. You will need to modify the export statement if your geonode source tree is 
located elsewhere. You may also need to modify the GEOSERVER_URL in the
runtests.sh script depending on your local setup.
