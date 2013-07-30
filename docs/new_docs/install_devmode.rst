Install GeoNode in development mode
===================================


In order to install Geonode 2.0 in developing mode on Ubuntu 12.04 the following steps are required:

* install build tools and libraries
* install dependencies (Python and Java) and supporting tools
* add PPA repository (for static development)
* set up a virtual environment (virtualenv)
* clone geonode from github and install it in the virtual environment
* compile geoserver and start the development servers 

*Remark*: The following steps have to be executed in your terminal. The *Steps 1 – 4a* have to be done as a root user, therefore don´t forget to type sudo in front (as shown in the steps)!

**Step 1**

The first step is to install required build tools and libraries::

    sudo apt-get install build-essential libxml2-dev libxslt-dev

**Step 2**

As known from installing former releases of Geonode, some dependencies and supporting tools have to be installed before Geonode can be set up.

*Python native dependencies*::

    sudo apt-get install python-dev python-virtualenv python-imaging python-lxml python-pyproj python-shapely python-nose python-httplib2

*Java dependencies*::

    sudo apt-get install -y --force-yes openjdk-6-jdk ant maven2 --no-install-recommends

*supporting tools*::

    sudo apt-get install -y git gettext

**Step 3**

Your third step is to add a new PPA repository, which is required for the static development::

    sudo add-apt-repository ppa:chris-lea/node.js
    sudo apt-get update
    sudo apt-get install nodejs
    sudo npm install -g less
    sudo npm install -g bower
    sudo npm install -g bower-installer

**Step 4** 

Now a virtual environment has to be set up, in which Geonode will later be running. Virtualenv has already been installed during *Step 2 (Python dependencies)*. Now you need to download and install a virutalenvwrapper (*Step 4a*), which has to be added to your environment (*Step 4b*). Before you can download and install Geonode, you have to set up the local virtual environment for Geonode (*Step 4c*).

*Step 4a*::

    sudo pip install virtualenvwrapper

*Step 4b*::

    export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python
    export WORKON_HOME=~/.venvs
    source /usr/local/bin/virtualenvwrapper.sh
    export PIP_DOWNLOAD_CACHE=$HOME/.pip-downloads

*Step 4c*::

        mkvirtualenv geonode
        workon geonode

**Step 5**

To download the latest geonode version from github, the command *clone* is used::

    git clone https://github.com/GeoNode/geonode.git

**Step 6**

You can now install Geonode in your local virtual environment. This process may take some time::

    pip install -e geonode --use-mirrors

In order to go on and complete the installation you have to direct to your now exisiting geonode folder::

    cd geonode

**Step 7**

The last step is to compile GeoServer and start the development servers::

    paver setup
    paver start

Now you should be able to visit the geonode site by typing ​http://localhost:8000 into your browser window.


***Important notice***

With every restart of your machine, you have to restart geonode as well! That means, you will not be able to open ​http://localhost:8000 directly after starting your machine new. In order to be able to use geonode now, you have to do the command *paver start* each time you want to use geonode! 

.. note:: *your_name* is the name of your machine and personal folder!

**Step a - Activate geonode virtualenv**
 
To do so you have to first activate your virtual environment for geonode. Therefore go to the folder where your virtualenv for geonode has been installed (this is usually .venvs) and direct to /geonode/bin, like this::

   cd /home/your_name/.venvs/geonode/bin

(but be careful with this, it really depends on where you have installed the virtualenv!)

Now type::

  source activate

and your virtualenv will be activated.

The recent path in your terminal should now look something like this::

  (geonode)your_name@your_name-VirtualBox:~/.venvs/geonode/bin



**Step b - Start the server**
  
In order to run the command paver start you now have to go back out from the *.venvs* folder and into the *geonode* folder, which is placed outside the virtualenv!

Therefore type::

  cd ..

until you are here::

  (geonode)your_name@your_name-VirtualBox:~

then use::

  cd geonode

and you will land here::

  (geonode)your_name@your_name-VirtualBox:~/geonode

and be able to run::

   paver start

Now you are able to access ​http://localhost8000 again.

.. note:: Remember that you have to do these steps each time you restart your machine!!

