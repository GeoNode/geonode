# Setup environment variables.
PATH=/home/jenkins/apache-maven-2.2.1/bin/:$PATH
MAVEN_HOME=/home/jenkins/apache-maven-2.2.1/
JAVA_HOME=/usr/lib/jvm/java-6-sun/
PYENV_HOME=$HOME/.pyenv/
DL_ROOT=/var/www/geonode/dev
GIT_REV=$(git log -1 --pretty=format:%h)

# Delete previously built virtualenv
if [ -d $PYENV_HOME ]; then
    rm -rf $PYENV_HOME
fi

# Setup the virtualenv
virtualenv --no-site-packages $PYENV_HOME
source $PYENV_HOME/bin/activate

# Make the debian package
if [ -d $DL_ROOT/$GIT_REV ]; then
    rm -rf $DL_ROOT/$GIT_REV
fi

# Setup and Build GeoNode
git clean -dxff
pip install -e .
#pip install -r requirements.txt --no-deps
paver setup

# Make the Debian package (locally)
paver deb
mkdir $DL_ROOT/$GIT_REV
cp *.deb $DL_ROOT/$GIT_REV/.
cp *.build $DL_ROOT/$GIT_REV/.
cp *.changes $DL_ROOT/$GIT_REV/.
cp package/*.gz $DL_ROOT/$GIT_REV/.

# Make the Debian package (upload to ppa)
paver deb -p geonode/unstable

rm -rf $DL_ROOT/latest
ln -sf $DL_ROOT/$GIT_REV $DL_ROOT/latest
