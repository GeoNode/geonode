# Setup environment variables.
MAVEN_HOME=/usr/share/maven
JAVA_HOME=/usr/lib/jvm/java-7-oracle/
PYENV_HOME=$HOME/.pyenv-master/
DL_ROOT=/var/www/geonode
GIT_REV=$(git log -1 --pretty=format:%h)

# Delete previously built virtualenv
if [ -d $PYENV_HOME ]; then
    rm -rf $PYENV_HOME
fi

# Setup the virtualenv
virtualenv --system-site-packages $PYENV_HOME
. $PYENV_HOME/bin/activate

# Install build & test tools
pip install --quiet paver
pip install --quiet nosexcover
pip install --quiet pylint
pip install --quiet pyflakes
pip install --quiet clonedigger
pip install --quiet pep8

# Setup and Build GeoNode
git clean -dxff

# run this here while we have a clean dir.
#/usr/bin/sloccount --duplicates --wide --details geonode/ > sloccount.out 
#python /usr/local/bin/clokins.py --exclude-list-file=scripts/jenkins/clokins.exclude . > clokins.output

pip install -e .
# Just in case
paver stop
paver setup
cp /var/lib/jenkins/local_settings_with_coverage.py geonode/local_settings.py

. $PYENV_HOME/bin/activate #double check its activated.

# Run the smoke tests
python manage.py test geonode.tests.smoke
cp TEST-nose.xml smoke-TEST-nose.xml
cp coverage.xml smoke-coverage.xml
cp -R coverage smoke-coverage

# Run the unit tests
python manage.py test
cp TEST-nose.xml unit-TEST-nose.xml
cp coverage.xml unit-coverage.xml
cp -R coverage unit-coverage

# Run the integration tests
paver reset
cp /var/lib/jenkins/local_settings_with_coverage.py geonode/local_settings.py
. $PYENV_HOME/bin/activate #double check its activated.
paver test_integration
cp TEST-nose.xml integration-TEST-nose.xml
cp coverage.xml integration-coverage.xml
cp -R coverage integration-coverage

# Run the catalogue tests
paver test_integration -n geonode.tests.csw
cp TEST-nose.xml csw-TEST-nose.xml
cp coverage.xml csw-coverage.xml
cp coverage -R csw-coverage

# Run the javascript tests 
#paver test_javascript
#mv geonode/static/geonode/junit.xml ./javascript-TEST-nose.xml

# Run Code Quality Tools
export DJANGO_SETTINGS_MODULE=geonode.settings
pylint -f parseable geonode/ | tee pylint.out
pep8 --repeat geonode | tee pep8.out
find . -type f -iname "*.py" | egrep -v '^./tests/'|xargs pyflakes  > pyflakes.out || :
clonedigger --cpd-output . || :
mv output.xml clonedigger.out

# All done, clean up
git reset --hard
