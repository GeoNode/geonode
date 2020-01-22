How to Install GDAL for development
======================================

Summary of installation 
.......................

This section demonstrates a summarization of the steps to be followed in order to install GDAL 2.4.2 for development using python2.7 virtualenv with Ubuntu 18.04. The idea here is to install GDAL on the host machine and then refer to this installed version from the virtual environment to have identical versions.

.. note:: The following commands/steps will be executed on your terminal 

.. warning:: The installation here is meant to serve GeoNode installation for development

The steps to be followed are:
.............................

1- Install GDAL on your host environment

2- Validate your installation on the host machine 

3- From your python virtual environment, Run: pip install GDAL==$(gdal-config --version) --global-option=build_ext --global-option="-I/usr/include/gdal"

4- Validate installation from host and virtual environment


Installation steps

On a fresh Ubuntu 18.04 installation, we will be installing gdal version 2.4.2

1- Using the terminal in the host machine, run the following commands:

.. code-block:: shell

    $ sudo add-apt-repository ppa:ubuntugis/ppa && sudo apt-get update
    $ sudo apt-get install libgdal-dev python3-gdal

.. note:: Make sure you don't have a newer version on the software list under /et/apt/sources.list.d/

2- Validate the installed version by running the following commands:


.. code-block:: shell

    $ sudo gdal-config --version   #it should output 2.4.2 at this step
    $ python -c "from osgeo import gdal; print gdal.__version__"    #it should output 2.4.2 at this step

3- Install GDAL on your virtual environment by referring to the same version which we just installed on the host machine. To do that, you will need to run the following command during activated virtual environment session as follows:



.. code-block:: shell
    
    $ virtualenv -p python2.7 my_env   # To create a python2.7 virtual environment called my_env
    
    $ # inside my_env/bin, run the following command to activate the virtual environment we just created
    
    $ source activate
    
    $ cd /home/geonode/my_env
    
    $ export CPLUS_INCLUDE_PATH=/usr/include/gdal
    
    $ export C_INCLUDE_PATH=/usr/include/gdal
    
    $ pip install GDAL==2.4.2

4- Confirm the installation 

In order to validate the installation between the host and the virtual environment, run the following command on both the host machine and on the activated virtual environment. If the results were identical, then GDAL for development is installed correctly for GeoNode

.. code-block:: shell
    
    $ python -c "from osgeo import gdal; print gdal.__version__"       # outputs "2.4.2"

And from the activated environment:

.. code-block:: shell
    
    $ (my_env) python -c "from osgeo import gdal; print gdal.__version__"      # outputs "2.4.2"

