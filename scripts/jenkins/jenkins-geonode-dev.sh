# Setup environment variables.
PATH=/home/jenkins/apache-maven-2.2.1/bin/:$PATH
MAVEN_HOME=/home/jenkins/apache-maven-2.2.1/
JAVA_HOME=/usr/lib/jvm/java-6-sun/
PYENV_HOME=$HOME/.pyenv-dev/
DL_ROOT=/var/www/geonode
GIT_REV=$(git log -1 --pretty=format:%h)

# Delete previously built virtualenv
if [ -d $PYENV_HOME ]; then
    rm -rf $PYENV_HOME
fi

# Setup the virtualenv
virtualenv --system-site-packages $PYENV_HOME
source $PYENV_HOME/bin/activate

# Install test tools
pip install --quiet nosexcover
pip install --quiet pylint
pip install --quiet pyflakes
pip install --quiet clonedigger

# Setup and Build GeoNode
git clean -dxff
# run this here while we have a clean dir.
/usr/bin/sloccount --duplicates --wide --details geonode/ > sloccount.out 
python /usr/local/bin/clokins.py --exclude-list-file=scripts/jenkins/clokins.exclude . > clokins.output
pip install -e .
# Just in case
paver stop
paver setup
cp /var/lib/jenkins/local_settings_with_coverage.py geonode/local_settings.py

# Run the smoke tests
python manage.py test geonode.tests.smoke

# Run the unit tests
python manage.py test
cp TEST-nose.xml unit-TEST-nose.xml
cp coverage.xml unit-coverage.xml
cp -R coverage unit-coverage

# Run the integration tests
paver reset
cp /var/lib/jenkins/local_settings_with_coverage.py geonode/local_settings.py
source $PYENV_HOME/bin/activate #double check its activated.

paver test_integration
cp TEST-nose.xml integration-TEST-nose.xml
cp coverage.xml integration-coverage.xml
cp -R coverage integration-coverage

# Run the catalogue tests
#(Ariel disabled these on Jan 10, 2013 - he will re-enable them)
#paver test_integration -n geonode.tests.csw
#cp TEST-nose.xml csw-TEST-nose.xml
#cp coverage.xml csw-coverage.xml
#cp coverage -R csw-coverage

# Run the uploader integration tests
cp /var/lib/jenkins/local_settings_db_datastore.py geonode/upload/tests/local_settings.py
paver reset
paver start_geoserver
PGPASSWORD=geonode dropdb -h localhost -U geonode geonode
PGPASSWORD=geonode createdb -h localhost -U geonode geonode -T template_postgis
DJANGO_SETTINGS_MODULE=geonode.upload.tests.test_settings python manage.py migrate --noinput
DJANGO_SETTINGS_MODULE=geonode.upload.tests.test_settings python manage.py loaddata sample_admin
sleep 30
DELETE_LAYERS= REUSE_DB=1 DJANGO_SETTINGS_MODULE=geonode.upload.tests.test_settings python manage.py test geonode.upload.tests.integration
cp TEST-nose.xml upload-TEST-nose.xml
cp coverage.xml upload-coverage.xml
cp coverage -R upload-coverage

# Run the javascript tests 
paver test_javascript
mv geonode/static/geonode/junit.xml ./javascript-TEST-nose.xml

# Run Code Quality Tools
export DJANGO_SETTINGS_MODULE=geonode.settings
pylint -f parseable geonode/ | tee pylint.out
pep8 --repeat geonode | tee pep8.out
find . -type f -iname "*.py" | egrep -v '^./tests/'|xargs pyflakes  > pyflakes.out || :
clonedigger --cpd-output . || :
mv output.xml clonedigger.out

# All done, clean up
git reset --hard
