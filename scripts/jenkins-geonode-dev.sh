# Setup environment variables.
PATH=/home/jenkins/apache-maven-2.2.1/bin/:$PATH
MAVEN_HOME=/home/jenkins/apache-maven-2.2.1/
JAVA_HOME=/usr/lib/jvm/java-6-sun/
PYENV_HOME=$HOME/.pyenv/

# Delete previously built virtualenv
if [ -d $PYENV_HOME ]; then
    rm -rf $PYENV_HOME
fi

# Setup the virtualenv
virtualenv --no-site-packages $PYENV_HOME
. $PYENV_HOME/bin/activate

# Install test tools
pip install --quiet nosexcover
pip install --quiet pylint
pip install --quiet pyflakes
pip install --quiet clonedigger

paver stop

# Setup and Build GeoNode
git clean -dxff
pip install -e .
#pip install -r requirements.txt
paver setup
cp /home/jenkins/local_settings_with_coverage.py geonode/local_settings.py

# Run the unit tests
paver test
cp TEST-nose.xml unit-TEST-nose.xml
cp coverage.xml unit-coverage.xml
cp -R coverage unit-coverage

# Run the integration tests
paver test_integration
cp TEST-nose.xml integration-TEST-nose.xml
cp coverage.xml integration-coverage.xml
cp -R coverage integration-coverage

# Run the catalogue tests
cp /home/jenkins/local_settings_with_coverage.py geonode/local_settings.py
paver test_integration -n geonode.tests.csw
cp TEST-nose.xml csw-TEST-nose.xml
cp coverage.xml csw-coverage.xml
cp coverage -R csw-coverage

# Run Code Quality Tools
export DJANGO_SETTINGS_MODULE=geonode.settings
pylint -f parseable geonode/ | tee pylint.out
pep8 --repeat geonode | tee pep8.out
find . -type f -iname "*.py" | egrep -v '^./tests/'|xargs pyflakes  > pyflakes.out || :
clonedigger --cpd-output . || :
mv output.xml clonedigger.out
echo; echo ">>> Reporting FIXME's and TODO's in source code"
grep -n -R --exclude *.pyc --exclude *.log --exclude *.log.* TODO geonode > todo.out
grep -n -R --exclude *.pyc --exclude *.log --exclude *.log.* FIXME geonode > fixme.out

# All done, clean up
git reset --hard
