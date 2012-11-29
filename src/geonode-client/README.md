# GeoNode Client

This is the javascript client part of GeoNode.


## Debug Mode

Loads all scripts uncompressed.

    ant init
    ant debug

This will give you an application available at http://localhost:8080/ by
default.  You only need to run `ant init` once (or any time dependencies
change).

Note that http://localhost:8080/index.html is just a "Hello World" to
see if everything is configured correctly. This project is not intended to run
standalone. Instead, it is meant to be used by GeoNode. To make GeoNode use it
instead of the static, minified JavaScript resources, make your GeoNode's
src/GeoNodePy/geonode/local_settings.py point to it:

    GEONODE_CLIENT_LOCATION = "http://localhost:8080/"


## Prepare App for Deployment

To create a zip with the minified application run the following:

    ant zip

The archive will be assembled in the build directory. GeoNode's
setup_geonode_client paver task expects this zip to be available at
http://dev.geonode.org/dev-data/geonode-client.zip for the master branch, and
http://dev.geonode.org/dev-data/synth/geonode-client.zip for the synth branch.

For now, since we don't have a post-commit hook yet that automatically updates
these resources, if you are a core developer with access to dev.geonode.org,
please copy the most recent geonode-client.zip to
/var/www/dev.geonode.org/htdocs/dev-data/(synth/) after a commit.
