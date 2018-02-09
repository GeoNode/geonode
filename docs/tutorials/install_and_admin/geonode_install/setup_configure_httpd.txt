.. _setup_configure_httpd:

=======================
Setup & Configure HTTPD
=======================

In this section we are going to setup Apache HTTP to serve GeoNode.

Preliminary Steps & Checks
==========================

#. Be sure **development (DEV)** mode has been stopped

    **If not already active** let's activate the new `geonode` Python Virtual Environment:

    .. code-block:: bash
        
        $ workon geonode

    Move into the `geonode` home folder

    .. code-block:: bash

        $ cd /home/geonode

    Move into the ``my_geonode`` custom project base folder

    .. code-block:: bash

        $ cd my_geonode

    **If** ``paver start`` **command is running** you need to stop it

    .. code-block:: bash

        $ paver stop

#. Restore site settings

    You need to restore initial customizations of the `my_geonode` ``local_settings``.
    In order to do that, edit the ``my_geonode/local_settings.py`` file:

        .. code-block:: bash

            $ vim my_geonode/local_settings.py
        
        Un-comment the following pieces
        
        .. code-block:: python

            ...
            SITEURL = 'http://localhost'
            ...
            GEOSERVER_LOCATION = os.getenv(
                'GEOSERVER_LOCATION', '{}/geoserver/'.format(SITEURL)
            )

            GEOSERVER_PUBLIC_LOCATION = os.getenv(
                'GEOSERVER_PUBLIC_LOCATION', '{}/geoserver/'.format(SITEURL)
            )
            ...

Apache Configuration
====================
Navigate to Apache configurations folder

.. code-block:: bash

    $ cd /etc/apache2/sites-available

And create a new configuration file for GeoNode:

.. code-block:: bash

    $ sudo vim geonode.conf

Place the following content inside the file

.. code-block:: yaml

    WSGIDaemonProcess geonode python-path=/home/geonode/my_geonode:/home/geo/Envs/geonode/lib/python2.7/site-packages user=www-data threads=15 processes=2

    <VirtualHost *:80>
        ServerName http://localhost
        ServerAdmin webmaster@localhost
        DocumentRoot /home/geonode/my_geonode/my_geonode

        LimitRequestFieldSize 32760
        LimitRequestLine 32760
    
        ErrorLog /var/log/apache2/error.log
        LogLevel warn
        CustomLog /var/log/apache2/access.log combined

        WSGIProcessGroup geonode
        WSGIPassAuthorization On
        WSGIScriptAlias / /home/geonode/my_geonode/my_geonode/wsgi.py

        Alias /static/ /home/geonode/my_geonode/my_geonode/static_root/
        Alias /uploaded/ /home/geonode/my_geonode/my_geonode/uploaded/

        <Directory "/home/geonode/my_geonode/my_geonode/">
             <Files wsgi.py>
                 Order deny,allow
                 Allow from all
                 Require all granted
             </Files>

            Order allow,deny
            Options Indexes FollowSymLinks
            Allow from all
            IndexOptions FancyIndexing
        </Directory>

        <Directory "/home/geonode/my_geonode/my_geonode/static_root/">
            Order allow,deny
            Options Indexes FollowSymLinks
            Allow from all
            Require all granted
            IndexOptions FancyIndexing
        </Directory>

        <Directory "/home/geonode/my_geonode/my_geonode/uploaded/thumbs/">
            Order allow,deny
            Options Indexes FollowSymLinks
            Allow from all
            Require all granted
            IndexOptions FancyIndexing
        </Directory>

        <Directory "/home/geonode/my_geonode/my_geonode/uploaded/avatars/">
            Order allow,deny
            Options Indexes FollowSymLinks
            Allow from all
            Require all granted
            IndexOptions FancyIndexing
        </Directory>

        <Directory "/home/geonode/my_geonode/my_geonode/uploaded/people_group/">
            Order allow,deny
            Options Indexes FollowSymLinks
            Allow from all
            Require all granted
            IndexOptions FancyIndexing
        </Directory>

        <Directory "/home/geonode/my_geonode/my_geonode/uploaded/group/">
            Order allow,deny
            Options Indexes FollowSymLinks
            Allow from all
            Require all granted
            IndexOptions FancyIndexing
        </Directory>

        <Directory "/home/geonode/my_geonode/my_geonode/uploaded/documents/">
            Order allow,deny
            Options Indexes FollowSymLinks
            Allow from all
            Require all granted
            IndexOptions FancyIndexing
        </Directory>
        
        <Directory "/home/geonode/my_geonode/my_geonode/uploaded/layers/">
            Order allow,deny
            Options Indexes FollowSymLinks
            Allow from all
            Require all granted
            IndexOptions FancyIndexing
        </Directory>

        <Proxy *>
            Order allow,deny
            Allow from all
        </Proxy>

        ProxyPreserveHost On
        ProxyPass /geoserver http://127.0.0.1:8080/geoserver
        ProxyPassReverse /geoserver http://127.0.0.1:8080/geoserver

    </VirtualHost>

This sets up a VirtualHost in Apache HTTP server for GeoNode and a reverse proxy
for GeoServer.

.. note::

    In the case that GeoServer is running on a separate machine change the `ProxyPass`
    and `ProxyPassReverse` accordingly

Now load apache `poxy` module

.. code-block:: bash

    $ sudo a2enmod proxy_http

And enable geonode configuration file

.. code-block:: bash

    $ sudo a2ensite geonode

Postfix Configuration
=====================
Postfix is a service allowing the host to send e-mail and notificaions to the users.
In order to make GeoNode being able to send e-mails you will need to enable the service.

.. code-block:: bash

    $ sudo ufw disable
    # This will be switch-off the 

Edit the ``postfix`` configuration in order to allow the service act as a web service

.. code-block:: bash

    $ sudo vim /etc/postfix/main.cf
    
Check that at the end of the file the following properties are configured as follows

.. code-block:: bash

    $ sudo vim /etc/postfix/main.cf

        ...
        recipient_delimiter = +
        inet_interfaces = all
        inet_protocols = all

Finally restart the ``postfix`` service

.. code-block:: bash

    $ sudo service postfix restart

Finalize GeoNode Setup
======================
Once the Apache2 Virtual Host has been correctly configured, we can finalize the `GeoNode` setup.

**If not already active** let's activate the new `geonode` Python Virtual Environment:

.. code-block:: bash
    
    $ workon geonode

Move into the `geonode` home folder

.. code-block:: bash

    $ cd /home/geonode

Move into the ``my_geonode`` custom project base folder

.. code-block:: bash

    $ cd my_geonode

First of all we need to tweak a bit the `my_geonode` ``local_settings``.
In order to do that, edit the ``my_geonode/local_settings.py`` file:

    .. code-block:: bash

        $ vim my_geonode/local_settings.py
    
    Double check that exitsting properties match the following and add the missing ones
    
    .. code-block:: python

        SITEURL = 'http://localhost'
        ...
        # account registration settings
        ACCOUNT_OPEN_SIGNUP = True
        ACCOUNT_APPROVAL_REQUIRED = False
        ACCOUNT_EMAIL_CONFIRMATION_EMAIL = False
        ACCOUNT_EMAIL_CONFIRMATION_REQUIRED = False

        # notification settings
        NOTIFICATION_ENABLED = False
        NOTIFICATION_LANGUAGE_MODULE = "account.Account"

        # Queue non-blocking notifications.
        NOTIFICATION_QUEUE_ALL = False

        # pinax.notifications
        # or notification
        NOTIFICATIONS_MODULE = 'pinax.notifications'

        if NOTIFICATION_ENABLED:
            INSTALLED_APPS += (NOTIFICATIONS_MODULE, )

        #Define email service on GeoNode
        EMAIL_ENABLE = False

        if EMAIL_ENABLE:
            EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
            EMAIL_HOST = 'localhost'
            EMAIL_PORT = 25
            EMAIL_HOST_USER = ''
            EMAIL_HOST_PASSWORD = ''
            EMAIL_USE_TLS = False
            DEFAULT_FROM_EMAIL = 'My GeoNode <no-reply@geonode.org>'

        # set to true to have multiple recipients in /message/create/
        USER_MESSAGES_ALLOW_MULTIPLE_RECIPIENTS = True

        INSTALLED_APPS = INSTALLED_APPS + ('my_geonode',)
        ...
        GEOSERVER_LOCATION = os.getenv(
            'GEOSERVER_LOCATION', '{}/geoserver/'.format(SITEURL)
        )

        GEOSERVER_PUBLIC_LOCATION = os.getenv(
            'GEOSERVER_PUBLIC_LOCATION', '{}/geoserver/'.format(SITEURL)
        )
        ...
        CATALOGUE = {
            'default': {
                # The underlying CSW implementation
                # default is pycsw in local mode (tied directly to GeoNode Django DB)
                'ENGINE': 'geonode.catalogue.backends.pycsw_local',
                # pycsw in non-local mode
                # 'ENGINE': 'geonode.catalogue.backends.pycsw_http',
                # GeoNetwork opensource
                # 'ENGINE': 'geonode.catalogue.backends.geonetwork',
                # deegree and others
                # 'ENGINE': 'geonode.catalogue.backends.generic',

                # The FULLY QUALIFIED base url to the CSW instance for this GeoNode
                'URL': '%s/catalogue/csw' % SITEURL,
                # 'URL': 'http://localhost:8080/geonetwork/srv/en/csw',
                # 'URL': 'http://localhost:8080/deegree-csw-demo-3.0.4/services',

                # login credentials (for GeoNetwork)
                'USER': 'admin',
                'PASSWORD': 'admin',
            }
        }
        ...
        
    In the end the ``my_geonode/local_settings.py`` should be something like this
    
    .. code-block:: python

        # -*- coding: utf-8 -*-
        #########################################################################
        #
        # Copyright (C) 2012 OpenPlans
        #
        # This program is free software: you can redistribute it and/or modify
        # it under the terms of the GNU General Public License as published by
        # the Free Software Foundation, either version 3 of the License, or
        # (at your option) any later version.
        #
        # This program is distributed in the hope that it will be useful,
        # but WITHOUT ANY WARRANTY; without even the implied warranty of
        # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
        # GNU General Public License for more details.
        #
        # You should have received a copy of the GNU General Public License
        # along with this program. If not, see <http://www.gnu.org/licenses/>.
        #
        #########################################################################

        # Django settings for the GeoNode project.
        import os
        from geonode.settings import *
        #
        # General Django development settings
        #

        # SECRET_KEY = '************************'

        SITEURL = 'http://localhost'
        SITENAME = 'my_geonode'

        # Defines the directory that contains the settings file as the LOCAL_ROOT
        # It is used for relative settings elsewhere.
        LOCAL_ROOT = os.path.abspath(os.path.dirname(__file__))

        MEDIA_ROOT = os.getenv('MEDIA_ROOT', os.path.join(LOCAL_ROOT, "uploaded"))

        STATIC_ROOT = os.getenv('STATIC_ROOT',
                                os.path.join(LOCAL_ROOT, "static_root")
                                )

        WSGI_APPLICATION = "my_geonode.wsgi.application"

        # Load more settings from a file called local_settings.py if it exists
        try:
            from local_settings import *
        except ImportError:
            pass

        # Additional directories which hold static files
        STATICFILES_DIRS.append(
            os.path.join(LOCAL_ROOT, "static"),
        )

        # Location of url mappings
        ROOT_URLCONF = 'my_geonode.urls'

        # Location of locale files
        LOCALE_PATHS = (
            os.path.join(LOCAL_ROOT, 'locale'),
            ) + LOCALE_PATHS


        # ######################################################################### #
        # account registration settings
        ACCOUNT_OPEN_SIGNUP = True
        ACCOUNT_APPROVAL_REQUIRED = False
        ACCOUNT_EMAIL_CONFIRMATION_EMAIL = False
        ACCOUNT_EMAIL_CONFIRMATION_REQUIRED = False

        # notification settings
        NOTIFICATION_ENABLED = False
        NOTIFICATION_LANGUAGE_MODULE = "account.Account"

        # Queue non-blocking notifications.
        NOTIFICATION_QUEUE_ALL = False

        # pinax.notifications
        # or notification
        NOTIFICATIONS_MODULE = 'pinax.notifications'

        if NOTIFICATION_ENABLED:
            INSTALLED_APPS += (NOTIFICATIONS_MODULE, )

        #Define email service on GeoNode
        EMAIL_ENABLE = False

        if EMAIL_ENABLE:
            EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
            EMAIL_HOST = 'localhost'
            EMAIL_PORT = 25
            EMAIL_HOST_USER = ''
            EMAIL_HOST_PASSWORD = ''
            EMAIL_USE_TLS = False
            DEFAULT_FROM_EMAIL = 'My GeoNode <no-reply@geonode.org>'

        # set to true to have multiple recipients in /message/create/
        USER_MESSAGES_ALLOW_MULTIPLE_RECIPIENTS = True
        # ######################################################################### #

        INSTALLED_APPS = INSTALLED_APPS + ('my_geonode',)

        TEMPLATES[0]['DIRS'].insert(0, os.path.join(LOCAL_ROOT, "templates"))

        # ########################################################################## #
        ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '::1']
        PROXY_ALLOWED_HOSTS = ("127.0.0.1", 'localhost', '::1')

        POSTGIS_VERSION = (2, 0, 7)

        DATABASES = {
            'default': {
                 'ENGINE': 'django.db.backends.postgresql_psycopg2',
                 'NAME': 'geonode',
                 'USER': 'geonode',
                 'PASSWORD': 'geonode',
             },
            # vector datastore for uploads
            'datastore' : {
                'ENGINE': 'django.contrib.gis.db.backends.postgis',
                #'ENGINE': '', # Empty ENGINE name disables
                'NAME': 'geonode_data',
                'USER' : 'geonode',
                'PASSWORD' : 'geonode',
                'HOST' : 'localhost',
                'PORT' : '5432',
            }
        }

        GEOSERVER_LOCATION = os.getenv(
            'GEOSERVER_LOCATION', '{}/geoserver/'.format(SITEURL)
        )

        GEOSERVER_PUBLIC_LOCATION = os.getenv(
            'GEOSERVER_PUBLIC_LOCATION', '{}/geoserver/'.format(SITEURL)
        )

        OGC_SERVER_DEFAULT_USER = os.getenv(
            'GEOSERVER_ADMIN_USER', 'admin'
        )

        OGC_SERVER_DEFAULT_PASSWORD = os.getenv(
            'GEOSERVER_ADMIN_PASSWORD', 'geoserver'
        )

        # OGC (WMS/WFS/WCS) Server Settings
        OGC_SERVER = {
            'default': {
                'BACKEND': 'geonode.geoserver',
                'LOCATION': GEOSERVER_LOCATION,
                'LOGIN_ENDPOINT': 'j_spring_oauth2_geonode_login',
                'LOGOUT_ENDPOINT': 'j_spring_oauth2_geonode_logout',
                # PUBLIC_LOCATION needs to be kept like this because in dev mode
                # the proxy won't work and the integration tests will fail
                # the entire block has to be overridden in the local_settings
                'PUBLIC_LOCATION': GEOSERVER_PUBLIC_LOCATION,
                'USER' : OGC_SERVER_DEFAULT_USER,
                'PASSWORD' : OGC_SERVER_DEFAULT_PASSWORD,
                'MAPFISH_PRINT_ENABLED' : True,
                'PRINT_NG_ENABLED' : True,
                'GEONODE_SECURITY_ENABLED' : True,
                'GEOGIG_ENABLED' : False,
                'WMST_ENABLED' : False,
                'BACKEND_WRITE_ENABLED': True,
                'WPS_ENABLED' : False,
                'LOG_FILE': '%s/geoserver/data/logs/geoserver.log' % os.path.abspath(os.path.join(PROJECT_ROOT, os.pardir)),
                # Set to dictionary identifier of database containing spatial data in DATABASES dictionary to enable
                'DATASTORE': 'datastore',
            }
        }

        CATALOGUE = {
            'default': {
                # The underlying CSW implementation
                # default is pycsw in local mode (tied directly to GeoNode Django DB)
                'ENGINE': 'geonode.catalogue.backends.pycsw_local',
                # pycsw in non-local mode
                # 'ENGINE': 'geonode.catalogue.backends.pycsw_http',
                # GeoNetwork opensource
                # 'ENGINE': 'geonode.catalogue.backends.geonetwork',
                # deegree and others
                # 'ENGINE': 'geonode.catalogue.backends.generic',

                # The FULLY QUALIFIED base url to the CSW instance for this GeoNode
                'URL': '%s/catalogue/csw' % SITEURL,
                # 'URL': 'http://localhost:8080/geonetwork/srv/en/csw',
                # 'URL': 'http://localhost:8080/deegree-csw-demo-3.0.4/services',

                # login credentials (for GeoNetwork)
                'USER': 'admin',
                'PASSWORD': 'admin',
            }
        }

        ALT_OSM_BASEMAPS = os.environ.get('ALT_OSM_BASEMAPS', False)
        CARTODB_BASEMAPS = os.environ.get('CARTODB_BASEMAPS', False)
        STAMEN_BASEMAPS = os.environ.get('STAMEN_BASEMAPS', False)
        THUNDERFOREST_BASEMAPS = os.environ.get('THUNDERFOREST_BASEMAPS', False)
        MAPBOX_ACCESS_TOKEN = os.environ.get('MAPBOX_ACCESS_TOKEN', None)
        BING_API_KEY = os.environ.get('BING_API_KEY', None)

        MAP_BASELAYERS = [{
            "source": {"ptype": "gxp_olsource"},
            "type": "OpenLayers.Layer",
            "args": ["No background"],
            "name": "background",
            "visibility": False,
            "fixed": True,
            "group":"background"
        },
        # {
        #     "source": {"ptype": "gxp_olsource"},
        #     "type": "OpenLayers.Layer.XYZ",
        #     "title": "TEST TILE",
        #     "args": ["TEST_TILE", "http://test_tiles/tiles/${z}/${x}/${y}.png"],
        #     "name": "background",
        #     "attribution": "&copy; TEST TILE",
        #     "visibility": False,
        #     "fixed": True,
        #     "group":"background"
        # },
        {
            "source": {"ptype": "gxp_osmsource"},
            "type": "OpenLayers.Layer.OSM",
            "name": "mapnik",
            "visibility": True,
            "fixed": True,
            "group": "background"
        }]

        LOCAL_GEOSERVER = {
            "source": {
                "ptype": "gxp_wmscsource",
                "url": OGC_SERVER['default']['PUBLIC_LOCATION'] + "wms",
                "restUrl": "/gs/rest"
            }
        }
        baselayers = MAP_BASELAYERS
        MAP_BASELAYERS = [LOCAL_GEOSERVER]
        MAP_BASELAYERS.extend(baselayers)

        LOGGING = {
            'version': 1,
            'disable_existing_loggers': True,
            'formatters': {
                'verbose': {
                    'format': '%(levelname)s %(asctime)s %(module)s %(process)d '
                              '%(thread)d %(message)s'
                },
                'simple': {
                    'format': '%(message)s',
                },
            },
            'filters': {
                'require_debug_false': {
                    '()': 'django.utils.log.RequireDebugFalse'
                }
            },
            'handlers': {
                'null': {
                    'level': 'ERROR',
                    'class': 'django.utils.log.NullHandler',
                },
                'console': {
                    'level': 'DEBUG',
                    'class': 'logging.StreamHandler',
                    'formatter': 'simple'
                },
                'mail_admins': {
                    'level': 'ERROR', 'filters': ['require_debug_false'],
                    'class': 'django.utils.log.AdminEmailHandler',
                }
            },
            "loggers": {
                "django": {
                    "handlers": ["console"], "level": "ERROR", },
                "geonode": {
                    "handlers": ["console"], "level": "DEBUG", },
                "gsconfig.catalog": {
                    "handlers": ["console"], "level": "DEBUG", },
                "owslib": {
                    "handlers": ["console"], "level": "DEBUG", },
                "pycsw": {
                    "handlers": ["console"], "level": "ERROR", },
                },
            }
        # ########################################################################## #

Finalize HTTPD Setup
====================

.. warning:: Those steps must be completed from folder ``/home/geonode/my_geonode`` and inside `geonode` Python Virtual Environment.

Dowload GeoNode data to be served by Apache. You will be prompted for confirmation

.. code-block:: bash

    $ python manage.py migrate
    $ python manage.py collectstatic

Add thumbs and layers folders

.. code-block:: bash

    $ sudo mkdir -p /home/geonode/my_geonode/my_geonode/uploaded/thumbs
    $ sudo mkdir -p /home/geonode/my_geonode/my_geonode/uploaded/layers

Change permissions on GeoNode files and folders to allow Apache to read and edit them

.. code-block:: bash

    $ sudo chown -Rf geonode /home/geonode/my_geonode/
    $ sudo chown -Rf geonode:www-data /home/geonode/my_geonode/my_geonode/static/
    $ sudo chown -Rf geonode:www-data /home/geonode/my_geonode/my_geonode/uploaded/
    $ chmod -Rf 777 /home/geonode/my_geonode/my_geonode/uploaded/thumbs
    $ chmod -Rf 777 /home/geonode/my_geonode/my_geonode/uploaded/layers
    $ sudo chown www-data:www-data /home/geonode/my_geonode/my_geonode/static_root/

Finally restart Apache to load the new configuration:

.. code-block:: bash

    $ sudo service apache2 restart
