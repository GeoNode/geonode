*****************************
How to start with data-docker
*****************************

What you can do with this docker container
==========================================

The **data-docker** project can be your base data container volume to add data from scratch to GeoServer and PostGIS and then make them persisted when you want to stop your current containers.

Quick introduction on creating persisted storage in Docker
==========================================================

Data persistence strategies
---------------------------

The most commonly used approches in `Docker`_ are `Data volumes`_ and `Data volume containers`_ which essentially create a file system data volume rather than a dedicated data volume container.

.. _Docker: https://www.docker.com/technologies/overview

.. warning:: If you want to follow this readme and run the docker command you have to make sure that your docker host environment has been already set and your docker default machine has been started.

.. note:: This is required by all developers who are using `Docker-Machine`_ for running containers. Those use native linux or vm like `Docker for Mac`_ and `Docker for Windows`_ don't need these checks.

.. _Docker-Machine: https://docs.docker.com/machine/
.. _Docker for Mac: https://www.docker.com/docker-mac
.. _Docker for Windows: https://www.docker.com/docker-windows

Docker-Machine
--------------

In order to verify base prerequirements please run this commands below:

.. code-block:: console

    $ docker-machine env

which should output something similar:

.. code-block:: console

    export DOCKER_TLS_VERIFY="1"
    export DOCKER_HOST="tcp://192.168.99.100:2376"
    export DOCKER_CERT_PATH="<user home>/.docker/machine/machines/default"
    export DOCKER_MACHINE_NAME="default"

and then configure your shell environment

.. code-block:: console

    $ eval $(docker-machine env)

Data volumes
------------

You can easily add a data volume to a container using the option `-v` with the command `run` as the example below:

.. code-block:: console

    $ docker run -d -P --name geonode-data-container -v /data geonode/geonode-data touch /data/test.txt

Which creates a data volume within the new container in the `/data` directory. Data volumes are very useful because can be shared and included into other containers. It can be also remarked that the volume created will persist the `test.txt` file.

Host data volumes
^^^^^^^^^^^^^^^^^

You can also mount a directory from your Docker daemon’s host into a container and this could be very useful for testing but even for production in case your host machine can share a storage mount point like a network file system (*NFS*). This approach despite its ease to implement nature has actually an heavy constraint that you have to pre-configure the mount point in your docker host.
This breaks two of the biggest Docker advantages: **container portability** and **applications run anywhere**.

.. code-block:: console

    $ docker run -d -P --name geonode-data-container -v /geonode_data/data:/data geonode/geonode-data touch /data/test.txt

In case of the GeoNode *data* for example you cannot start from scratch in development like you actually do with

.. code-block:: console

    (venv)$ paver reset_hard

Data volume containers
----------------------
A data volume container is essentially a docker image that defines storage space. The container itself just defines a place inside docker's virtual file system where data is stored. The container doesn’t run a process and in fact *stops* immediately after `docker run` is called as the container exists in a stopped state, so along with its data.

So let's create a dedicated container that holds all of GeoNode persistent shareable data resources, mounting the data inside of it and then eventually into other containers once created and setup:

.. code-block:: console

    $ docker create -v /geonode-store --name geonode-data-container geonode/geonode-data /bin/true

.. note:: `/bin/true` returns a `0` and does nothing if the command was successful.

And the with the option `--volumes-from` you can mount the created volume `/geonode-store` within other containers by running:

.. code-block:: console

    $ docker run -d --volumes-from geonode-data-container --name geoserver geonode/geoserver

.. hint:: Notice that if you remove containers that mount volumes, the volume store and its data will not be deleted since docker preserves that.

To completely delete a volume from the file system you have to run:

.. code-block:: console

    $ docker rm -v geoserver

How to start with docker-compose for geonode data volume container
==================================================================

Start the creation of a volume with the **GEOSERVER_DATA_DIR** in the directory `/geoserver_data/data`:

.. code-block:: console

    $ docker-compose up

Run a geoserver container with such created volume:

.. code-block:: console

	# need to having pulling geonode/geoserver:2.10.x from docker hub
    $ docker run -d --volumes-from geoserver_data_dir --name geoserver geonode/geoserver

Verify that the preloaded `GeoServer Data Directory for GeoServer 2.15.x`_ build from Jenkins is actually there:

.. _GeoServer Data Directory for GeoServer 2.15.x: http://build.geonode.org/geoserver/latest/data-2.15.x.zip

.. code-block:: console

    $ docker exec -it geoserver ls -lart /geoserver_data/data/

The output should be something similar:

.. code-block:: console

	total 76
	drwxr-xr-x  3 root root 4096 Aug 27 16:51 workspaces
	-rw-r--r--  1 root root 1547 Aug 27 16:51 wms.xml
	-rw-r--r--  1 root root 2013 Aug 27 16:51 wfs.xml
	-rw-r--r--  1 root root 1285 Aug 27 16:51 wcs.xml
	drwxr-xr-x  2 root root 4096 Aug 27 16:51 styles
	drwxr-xr-x  8 root root 4096 Aug 27 16:51 security
	drwxr-xr-x  2 root root 4096 Aug 27 16:51 printing
	drwxr-xr-x  2 root root 4096 Aug 27 16:51 plugIns
	drwxr-xr-x  2 root root 4096 Aug 27 16:51 palettes
	drwxr-xr-x  2 root root 4096 Aug 27 16:51 logs
	-rw-r--r--  1 root root  144 Aug 27 16:51 logging.xml
	drwxr-xr-x  2 root root 4096 Aug 27 16:51 images
	-rw-r--r--  1 root root 1111 Aug 27 16:51 gwc-gs.xml
	-rw-r--r--  1 root root 1374 Aug 27 16:51 global.xml
	drwxr-xr-x  2 root root 4096 Aug 27 16:51 geonode
	drwxr-xr-x  2 root root 4096 Aug 27 16:51 demo
	-rw-r--r--  1 root root  184 Aug 27 16:51 README.rst
	drwxr-xr-x 12 root root 4096 Aug 27 16:51 .
	drwxr-xr-x  7 root root 4096 Aug 27 17:08 ..

How to define a docker-compose that uses data-docker
----------------------------------------------------

A docker-compose.yml can be defined in such a way with a service that mounts this data directory from a `tag of Docker Hub builds`_, in this case the version for `GeoServer-GeoNode 2.15.x`_:

.. _tag of Docker Hub builds: https://hub.docker.com/r/geonode/geoserver_data/builds/

.. _GeoServer-GeoNode 2.15.x: https://github.com/GeoNode/geoserver-geonode-ext/tree/2.15.x

.. code-block:: yaml

    version: '2'

    services:
        geoserver:
            build: .
            ports:
                - "8888:8080"
            volumes_from:
                # reference to the service which has the volume with the preloaded geoserver_data_dir
                - data_dir_conf
        data_dir_conf:
            image: geonode/geoserver_data:2.15.x
            container_name: geoserver_data_dir # named data container
            command: /bin/true
            volumes:
                - /geoserver_data/data

    volumes:
        # reference to the named data container that holds the preloaded geoserver data directory
        geoserver_data_dir:


Available tags
--------------

There are several different tags from the `Docker Hub builds`_:

.. _Docker Hub builds: https://cloud.docker.com/u/geonode/repository/registry-1.docker.io/geonode/geoserver_data/builds/

* **2.9.x**: `geonode/geoserver_data:2.9.x`_
* **2.9.x-oauth2**: `geonode/geoserver_data:2.9.x-oauth2`_
* **2.10.x**: `geonode/geoserver_data:2.10.x`_
* **2.12.x**: `geonode/geoserver_data:2.12.x`_
* **2.13.x**: `geonode/geoserver_data:2.13.x`_
* **2.14.x**: `geonode/geoserver_data:2.14.x`_
* **2.15.x**: `geonode/geoserver_data:2.15.x`_

.. _geonode/geoserver_data:2.9.x: https://hub.docker.com/r/geonode/geoserver_data/builds/bsus6alnddg4bc7icwymevp/
.. _geonode/geoserver_data:2.9.x-oauth2: https://hub.docker.com/r/geonode/geoserver_data/builds/bwkxcupsunvuitzusi9gsnt/
.. _geonode/geoserver_data:2.10.x: https://hub.docker.com/r/geonode/geoserver_data/builds/b9vbumhwfcrti8bxnmpbpwi/
.. _geonode/geoserver_data:2.12.x: https://hub.docker.com/r/geonode/geoserver_data/builds/byaaalw3lnasunpveyg3x4i/
.. _geonode/geoserver_data:2.13.x: https://hub.docker.com/r/geonode/geoserver_data/builds/bunuqzq7a7dk65iumjhkbtc/
.. _geonode/geoserver_data:2.14.x: https://cloud.docker.com/u/geonode/repository/registry-1.docker.io/geonode/geoserver_data/builds/545f08f9-75a3-4161-bcb0-895c1817dc8d
.. _geonode/geoserver_data:2.15.x: https://cloud.docker.com/u/geonode/repository/registry-1.docker.io/geonode/geoserver_data/builds/dce29f95-b6f7-4f5e-86f1-78d5e98fd866
