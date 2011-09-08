Deploying on Ubuntu 10.04
=========================

For Ubuntu, GeoNode provides a .deb installer to fully automate the installation process.
It is also possible to use a tar archive for the installation; this provides a bit more flexibility about the configuration.
See :doc:/deploy/tarball for details.
If you aren't sure though, the .deb is the most reliable and easiest way.

Hosted Package
--------------

The easiest way to get the .deb is to install it using APT, the standard installation management tool for Ubuntu and other Debian-based systems.

1) Set up the OpenGeo repository (you only need to do this once; the repository will still be available for upgrades later)::

   $ sudo add-apt-repository deb http://apt.opengeo.org/ubuntu lucid main

2) Install the package. This step will also automatically download any needed dependencies::

   $ sudo apt-get update && sudo apt-get install geonode

 
Custom Package
--------------

In some circumstances (for example, if you built your own GeoNode deb with customizations included) it is useful to install a .deb file without it first being uploaded to a Debian repository.

1) Install the package directly using the dpkg tool.
   **This step will probably fail due to missing dependencies!**
   You can recover and finish the installation afterwards, see below.

   .. code-block:: bash

       $ sudo dpkg -i geonode_1.1-rc1+1_all.deb

2) Now you can ask apt-get to install all the missing dependencies and then resume the failed installation::

   $ sudo apt-get install -f
