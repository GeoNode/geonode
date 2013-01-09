#!/bin/bash

git checkout -b i18n

# Setup environment variables.
PYENV_HOME=$HOME/.pyenv/

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
msg="Daily Update GeoNode i18n "`eval date +%Y%m%d%H%M%S`
git commit -am "$msg"
git push git@github.com:jj0hns0n/geonode.git i18n

# Send the PR against GeoNode dev (Need to export username and password as env vars)
hub pull-request -f "Daily Update GeoNode i18n" -b GeoNode/geonode:dev -h jj0hns0n/geonode:i18n

# Push everything back to Transifex
tx push -s --skip
