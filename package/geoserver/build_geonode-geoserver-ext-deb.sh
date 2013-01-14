#!/bin/bash

set -e

DL_ROOT=/var/www/geoserver

# Make sure last job cleaned up
if [ -d ./tmp ]; then
  rm -rf ./tmp
fi

# Checkout exts from server
GEOSERVER_EXT_GIT=git://github.com/GeoNode/geoserver-geonode-ext.git
git clone $GEOSERVER_EXT_GIT tmp

cp -r debian tmp
pushd tmp

GIT_REV=$(git log -1 --pretty=format:%h)

# Build for launchpad
debuild -S
dput ppa:geonode/unstable ../geoserver-geonode_2.0_source.changes
rm ../geoserver-geonode*

# Re-build local debs
debuild

# Copy .debs, .jar, and .war into place on the server
if [ -d $DL_ROOT/$GIT_REV ]; then
    rm -rf $DL_ROOT/$GIT_REV
fi

mkdir $DL_ROOT/$GIT_REV
cp ../*.deb $DL_ROOT/$GIT_REV/.
cp target/geoserver.war $DL_ROOT/$GIT_REV/.
cp target/geonode-geoserver-ext-*-geoserver-plugin.zip $DL_ROOT/$GIT_REV/.
cp target/data*.zip $DL_ROOT/$GIT_REV/data.zip

# Remove all but last 4 builds to stop disk from filling up
(ls -t|tail -n 3)|sort|uniq -u | xargs rm -rf

# Cleanup
rm -rf $DL_ROOT/latest
ln -sf $DL_ROOT/$GIT_REV $DL_ROOT/latest
rm ../geoserver-geonode*

popd
rm -rf tmp