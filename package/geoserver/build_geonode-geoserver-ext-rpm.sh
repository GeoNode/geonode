#!/bin/bash

set -e

export GEONODE_EXT_ROOT=$PWD/tmp
DL_ROOT=/var/www/geoserver

# Make sure last job cleaned up
if [ -d ./tmp ]; then
  rm -rf ./tmp
fi

# Checkout exts from server
GEOSERVER_EXT_GIT=git://github.com/GeoNode/geoserver-geonode-ext.git
git clone $GEOSERVER_EXT_GIT tmp

cp -r rpm tmp
pushd tmp
GIT_REV=$(git log -1 --pretty=format:%h)

# Build RPM
rpmbuild --define "_topdir ${PWD}/rpm" -bb rpm/SPECS/geoserver.spec

# Copy .rpms into place on the server
scp -P 7777 -i ~/.ssh/jenkins_key.pem ../*.rpm jenkins@build.geonode.org:$DL_ROOT/$GIT_REV

# Cleanup
rm ../*.rpm

popd
rm -rf tmp
