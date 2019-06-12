Overview
========

The following steps will guide you to a fresh setup of GeoNode Project. All guides will first install and configure the system to run it in ``DEBUG`` mode (also known as ``DEVELOPMENT`` mode) and then by configuring an HTTPD server to serve GeoNode through the standard ``HTTP`` (``80``) port.

Those guides **are not** meant to be used on a production system. There will be dedicated chapters that will show you some *hints* to optimize GeoNode for a production-ready machine. In any case, we strongly suggest to task an experienced *DevOp* or *System Administrator* before exposing your server to the ``WEB``.

Ubuntu 18.04
============

TODO

Docker
======

.. warning:: Before moving with this section, you should have read and clearly understood the ``INSTALLATION > GeoNode Core`` sections, and in particular the ``Docker`` one. Everything said for the GeoNode Core Vanilla applies here too, except that the Docker container names will be slightly different. As an instance if you named your project ``my_geonode``, you containers will be called:

  .. code-block:: shell
  
    'django4my_geonode' instead of 'django4geonode' and so on...

Deploy an instance of a geonode-project Django template 2.10.x with Docker on localhost
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Prepare the environment

.. code-block:: shell

  sudo mkdir -p /opt/geonode_custom/
  sudo usermod -a -G www-data geonode
  sudo chown -Rf geonode:www-data /opt/geonode_custom/
  sudo chmod -Rf 775 /opt/geonode_custom/

Clone the source code

.. code-block:: shell

  cd /opt/geonode_custom/
  git clone https://github.com/GeoNode/geonode-project.git

Make an instance out of the ``Django Template``

.. note:: We will call our istance ``my_geonode``. You can change the name at your convenience.

.. code-block:: shell

  mkvirtualenv my_geonode
  pip install Django==1.11.20
  django-admin startproject --template=./geonode-project -e py,rst,json,yml,ini,env,sample -n Dockerfile my_geonode
  cd /opt/geonode_custom/my_geonode

Modify the code and the templates and rebuild the Docker Containers

.. code-block:: shell
  
  docker-compose -f docker-compose.yml -f docker-compose.override.yml build --no-cache

Finally run the containers

.. code-block:: shell
  
  docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d

Deploy an instance of a geonode-project Django template 2.10.x with Docker on a domain
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. note:: We will use ``www.example.org`` as an example. You can change the name at your convenience.

Stop the containers

.. code-block:: shell

  cd /opt/geonode_custom/my_geonode
  
  docker-compose -f docker-compose.yml -f docker-compose.override.yml stop
  
Edit the ``ENV`` override file in order to deploy on ``www.example.org``

.. code-block:: shell

  # Make a copy of docker-compose.override.yml
  cp docker-compose.override.yml docker-compose.override.example-org.yml
    
Replace everywhere ``localhost`` with ``www.example.org``

.. code-block:: shell

  vim docker-compose.override.example-org.yml
  
.. code-block:: shell

  # e.g.: :%s/localhost/www.example.org/g
  
  version: '2.2'
  services:

    django:
      build: .
      # Loading the app is defined here to allow for
      # autoreload on changes it is mounted on top of the
      # old copy that docker added when creating the image
      volumes:
        - '.:/usr/src/my_geonode'
      environment:
        - DEBUG=False
        - GEONODE_LB_HOST_IP=www.example.org
        - GEONODE_LB_PORT=80
        - SITEURL=http://www.example.org/
        - ALLOWED_HOSTS=['www.example.org', ]
        - GEOSERVER_PUBLIC_LOCATION=http://www.example.org/geoserver/
        - GEOSERVER_WEB_UI_LOCATION=http://www.example.org/geoserver/

    geoserver:
      environment:
        - GEONODE_LB_HOST_IP=localhost
        - GEONODE_LB_PORT=80
    #    - NGINX_BASE_URL=


.. note:: It is possible to override here even more variables to customize the GeoNode instance. See the ``GeoNode Settings`` section in order to get a list of the available options.

Run the containers in daemon mode

.. code-block:: shell

  docker-compose -f docker-compose.yml -f docker-compose.override.example-org.yml up --build -d
