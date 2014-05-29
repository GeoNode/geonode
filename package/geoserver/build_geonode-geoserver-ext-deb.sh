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
git checkout $GIT_BRANCH

# Replace GeoNode port for production.
sed -i 's/localhost:8000/127.0.0.1/g' \
    src/main/java/org/geonode/security/GeoNodeSecurityProvider.java

git config user.email "mweisman@opengeo.org"
git config user.name "Michael Weisman"

GIT_REV=$(git log -1 --pretty=format:%h)

DEB_VERSION=2.0+$(date +"%Y%m%d%H%M")

mvn clean install war:war

# Build for launchpad
#git-dch --spawn-editor=snapshot --new-version=$DEB_VERSION --git-author --id-length=6 --ignore-branch  --auto --release
#sed -i 's/urgency=low/urgency=high/g' \
#    debian/changelog

#debuild -S
#dput ppa:geonode/$PPA ../geoserver-geonode_${DEB_VERSION}_source.changes
#rm ../geoserver-geonode*

# Re-build local debs
#debuild

# Copy .debs, .jar, and .war into place on the server
if [ -d $DL_ROOT/$GIT_REV ]; then
    rm -rf $DL_ROOT/$GIT_REV
fi

mkdir $DL_ROOT/$GIT_REV
#cp ../*.deb $DL_ROOT/$GIT_REV/.
cp target/geoserver.war $DL_ROOT/$GIT_REV/.
cp target/geonode-geoserver-ext-*-geoserver-plugin.zip $DL_ROOT/$GIT_REV/.
cp target/*data.zip $DL_ROOT/$GIT_REV/data.zip

# Remove all but last 4 builds to stop disk from filling up
(ls -t|tail -n 3)|sort|uniq -u | xargs rm -rf

# Cleanup
rm -rf $DL_ROOT/latest
ln -sf $DL_ROOT/$GIT_REV $DL_ROOT/latest
#rm ../geoserver-geonode*

popd
rm -rf tmp
