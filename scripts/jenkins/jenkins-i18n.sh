#!/bin/bash

# Setup environment variables.
source ~/.bashrc
PATH=/home/jenkins/apache-maven-2.2.1/bin/:$PATH
MAVEN_HOME=/home/jenkins/apache-maven-2.2.1/
JAVA_HOME=/usr/lib/jvm/java-6-sun/
PYENV_HOME=$HOME/.pyenv/
DL_ROOT=/var/www/geonode
GIT_REV=$(git log -1 --pretty=format:%h)

# Delete previously built virtualenv
if [ -d $PYENV_HOME ]; then
    rm -rf $PYENV_HOME
fi

# Setup the virtualenv
virtualenv --no-site-packages $PYENV_HOME
source $PYENV_HOME/bin/activate

# Install the transifex client manually
pip install transifex-client

# Install Django Manually
pip install Django

# Pull all latest changes from Transifex
tx pull --force --all

# Update the Django i18n files
cd geonode
python ../manage.py makemessages --all
python ../manage.py compilemessages
git add .
git commit -am "Daily Update GeoNode i18n"
git push -u git@github.com:jj0hns0n/geonode.git HEAD:i18n

# Send the PR against GeoNode dev (Need to export username and password as env vars)
git pull-request -f "Daily Update GeoNode i18n" -b jj0hns0n/geonode:dev -h jj0hns0n/geonode:i18n

# Push everything back to Transifex
tx push -s --skip
