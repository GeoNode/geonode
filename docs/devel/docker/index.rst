Start to develop with Docker
----------------------------

How to run the instance for development
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Set the variable SET_DOCKER_ENV for development
...............................................

.. code-block:: shell

    vi .env

Change to

.. code-block:: shell

    SET_DOCKER_ENV=development

Use dedicated docker-compose files while developing
...................................................

.. note:: In this example we are going to keep ``localhost`` as the target IP for GeoNode

.. code-block:: shell

    docker-compose -f docker-compose.async.yml -f docker-compose.development.yml up

How to debug
............

.. note:: We are supposing to use ``ipdb`` for debugging which is already available as package from the container

Stop the container for the ``django`` service:

.. code-block:: shell

    docker-compose stop django

Run the container again with the option for *service ports*:

.. code-block:: shell

    docker-compose run \
        -e DOCKER_ENV=development \
        -e IS_CELERY=False \
        -e DEBUG=True \
        -e GEONODE_LB_HOST_IP=localhost \
        -e GEONODE_LB_PORT=80 \
        -e SITEURL=http://localhost/ \
        -e ALLOWED_HOSTS="['localhost', ]" \
        -e GEOSERVER_PUBLIC_LOCATION=http://localhost/geoserver/ \
        -e GEOSERVER_WEB_UI_LOCATION=http://localhost/geoserver/ \
        --rm --service-ports django python manage.py runserver --settings=geonode.settings 0.0.0.0:8000

Access the site on http://localhost/

.. note:: If you set an ``ipdb`` debug point with import ``ipdb ; ipdb.set_trace()`` then you should be facing its console and you can see the django server which is restarting at any change of your code from your local machine.