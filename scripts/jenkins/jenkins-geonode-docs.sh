#!/bin/bash

# Clean up from previous runs
rm -rf ${WORKSPACE}/*

# Setup environment variables.
PYENV_HOME=$HOME/.pyenv/

# Delete previously built virtualenv
if [ -d $PYENV_HOME ]; then
    rm -rf $PYENV_HOME
fi

# Setup the virtualenv
virtualenv --no-site-packages $PYENV_HOME
source $PYENV_HOME/bin/activate
pip install cactus
pip install sphinx_bootstrap_theme

# Get all the Relevant repos
git clone git@github.com:GeoNode/geonode.github.com.git
git clone git://github.com/GeoNode/geonode.git
git clone git://github.com/GeoNode/geonode-workshops.git

# Compile and Publish docs
cd geonode/docs
make html
make latexpdf
rm -rf /var/www/docs/*
cp -R _build/html/* /var/www/docs/
cp -R _build/latex/GeoNode.pdf /var/www/docs/

# Compile and Publish Workshops
cd ${WORKSPACE}/geonode-workshops/user/doc
make html
make latexpdf
rm -rf /var/www/workshops/user/*
cp -R build/html/* /var/www/workshops/user/
cp -R build/latex/GeoNodeUsersWorkshop.pdf /var/www/workshops/user/

cd ${WORKSPACE}/geonode-workshops/admin/doc
make html
make latexpdf
rm -rf /var/www/workshops/admin/*
cp -R build/html/* /var/www/workshops/admin/
cp -R build/latex/GeoNodeAdministratorsWorkshop.pdf /var/www/workshops/admin/

cd ${WORKSPACE}/geonode-workshops/devel/doc
make html
make latexpdf
rm -rf /var/www/workshops/devel/*
cp -R build/html/* /var/www/workshops/devel/
cp -R build/latex/GeoNodeDevelopersWorkshop.pdf /var/www/workshops/devel/

# Compile and Publish Website
cd ${WORKSPACE}/geonode.github.com/
cactus build
cp -R .build/* .

# Publish Workshops
echo "Publishing Workshops"
rm -rf workshops/*
echo "Publishing User Workshop"
mkdir workshops/user
cp -R ${WORKSPACE}/geonode-workshops/user/doc/build/html/* workshops/user/
cp -R ${WORKSPACE}/geonode-workshops/user/doc/build/latex/*.pdf workshops/user/
echo "Publishing admin Workshop"
mkdir workshops/admin
cp -R ${WORKSPACE}/geonode-workshops/admin/doc/build/html/* workshops/admin/
cp -R ${WORKSPACE}/geonode-workshops/admin/doc/build/latex/*.pdf workshops/admin/
echo "Publishing developer Workshop"
mkdir workshops/devel
cp -R ${WORKSPACE}/geonode-workshops/devel/doc/build/html/* workshops/devel/
cp -R ${WORKSPACE}/geonode-workshops/devel/doc/build/latex/*.pdf workshops/devel/
ls workshops/devel/
git add .
git commit -am "Update GeoNode Website"
git push origin master
rm -rf /var/www/site/*
cp -R .build/* /var/www/site/
