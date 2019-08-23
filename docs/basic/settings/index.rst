.. _settings:

========
Settings
========

Here’s a list of settings available in GeoNode and their default values.  This includes settings for some external applications that
GeoNode depends on.

For most of them, default values are good. Those should be changed only for advanced configurations in production or heavily hardened systems.

The most common ones can be set through ``environment`` variables to avoid touching the ``settings.py`` file at all.
This is a good practice and also the preferred one to configure GeoNode (and Django apps in general).
Whenever you need to change them, set the environment variable accordingly (where it is available) instead of overriding it through the ``local_settings``.

.. comment:
    :local:
    :depth: 1

A
=

ACCESS_TOKEN_EXPIRE_SECONDS
---------------------------

    | Default: ``86400``
    | Env: ``ACCESS_TOKEN_EXPIRE_SECONDS``

    When a user logs into GeoNode, if no ``ACCESS_TOKEN`` exists, a new one will be created with a default expiration time of ``ACCESS_TOKEN_EXPIRE_SECONDS`` seconds (1 day by default).

ACCOUNT_APPROVAL_REQUIRED
-------------------------

    | Default: ``False``
    | Env: ``ACCOUNT_APPROVAL_REQUIRED``

    If ``ACCOUNT_APPROVAL_REQUIRED`` equals ``True``, newly registered users must be activated by a superuser through the Admin gui, before they can access GeoNode.

ACCOUNT_CONFIRM_EMAIL_ON_GET
----------------------------

    | Default: ``True``

    This is a `django-allauth setting <https://django-allauth.readthedocs.io/en/latest/configuration.html#configuration>`__
    It allows specifying the HTTP method used when confirming e-mail addresses.

ACCOUNT_EMAIL_REQUIRED
----------------------

    | Default: ``True``

    This is a `django-allauth setting <https://django-allauth.readthedocs.io/en/latest/configuration.html#configuration>`__
    which controls whether the user is required to provide an e-mail address upon registration.

ACCOUNT_EMAIL_VERIFICATION
--------------------------

    | Default: ``optional``

    This is a `django-allauth setting <https://django-allauth.readthedocs.io/en/latest/configuration.html#configuration>`__

ACCOUNT_LOGIN_REDIRECT_URL
--------------------------

    | Default: ``SITEURL``
    | Env: ``LOGIN_REDIRECT_URL``

    This is a `django-user-accounts setting <https://django-user-accounts.readthedocs.io/en/latest/settings.html>`__
    It allows specifying the default redirect URL after a successful login.

ACCOUNT_LOGOUT_REDIRECT_URL
---------------------------

    | Default: ``SITEURL``
    | Env: ``LOGOUT_REDIRECT_URL``

    This is a `django-user-accounts setting <https://django-user-accounts.readthedocs.io/en/latest/settings.html>`__
    It allows specifying the default redirect URL after a successful logout.

ACCOUNT_NOTIFY_ON_PASSWORD_CHANGE
---------------------------------

    | Default: ``True``
    | Env: ``ACCOUNT_NOTIFY_ON_PASSWORD_CHANGE``

    This is a `django-user-accounts setting <https://django-user-accounts.readthedocs.io/en/latest/settings.html>`__

ACCOUNT_OPEN_SIGNUP
-------------------

    | Default: ``True``

    This is a `django-user-accounts setting <https://django-user-accounts.readthedocs.io/en/latest/settings.html>`__
    Whether or not people are allowed to self-register to GeoNode or not.

ACTSTREAM_SETTINGS
------------------

    Default::

        {
        'FETCH_RELATIONS': True,
        'USE_PREFETCH': False,
        'USE_JSONFIELD': True,
        'GFK_FETCH_DEPTH': 1,
        }

    Actstream Settings.

ADMIN_MODERATE_UPLOADS
----------------------

    | Default: ``False``

    When this variable is set to ``True``, every uploaded resource must be approved before becoming visible to the public users.

    Until a resource is in ``PENDING APPROVAL`` state, only the superusers, owner and group members can access it, unless specific edit permissions have been set for other users or groups.

    A ``Group Manager`` *can* approve the resource, but he cannot publish it whenever the setting ``RESOURCE_PUBLISHING`` is set to ``True``.
    Otherwise, if ``RESOURCE_PUBLISHING`` is set to ``False``, the resource becomes accessible as soon as it is approved.

AGON_RATINGS_CATEGORY_CHOICES
-----------------------------

    Default::

        {
            "maps.Map": {
                "map": "How good is this map?"
                },
            "layers.Layer": {
                "layer": "How good is this layer?"
                },
            "documents.Document": {
            "document": "How good is this document?"
            }
        }


ALLOWED_DOCUMENT_TYPES
----------------------

    Default::

        ['doc', 'docx', 'gif', 'jpg', 'jpeg', 'ods', 'odt', 'odp', 'pdf', 'png',
        'ppt', 'pptx', 'rar', 'sld', 'tif', 'tiff', 'txt', 'xls', 'xlsx', 'xml',
        'zip', 'gz', 'qml']

    A list of acceptable file extensions that can be uploaded to the Documents app.

ANONYMOUS_USER_ID
-----------------

    | Default: ``-1``
    | Env: ``ANONYMOUS_USER_ID``

    The id of an anonymous user. This is an django-guardian setting.

API_INCLUDE_REGIONS_COUNT
-------------------------

    | Default: ``False``
    | Env: ``API_INCLUDE_REGIONS_COUNT``

    If set to ``True``, a counter with the total number of available regions will be added to the API JSON Serializer.

API_LIMIT_PER_PAGE
------------------

    | Default: ``200``
    | Env: ``API_LIMIT_PER_PAGE``

    The Number of items returned by the APIs 0 equals no limit. Different from ``CLIENT_RESULTS_LIMIT``, affecting the number of items per page in the resource list.

ASYNC_SIGNALS
-------------

    | Default: ``False``
    | Env: ``ACCOUNT_NOTIFY_ON_PASSWORD_CHANGE``

AUTH_EXEMPT_URLS
----------------

    Default::

        (r'^/?$',
        '/gs/*',
        '/static/*',
        '/o/*',
        '/api/o/*',
        '/api/roles',
        '/api/adminRole',
        '/api/users',
        '/api/layers',)

    A tuple of URL patterns that the user can visit without being authenticated.
    This setting has no effect if ``LOCKDOWN_GEONODE`` is not True.  For example,
    ``AUTH_EXEMPT_URLS = ('/maps',)`` will allow unauthenticated users to
    browse maps.

AUTO_GENERATE_AVATAR_SIZES
--------------------------

    Default: ``20, 30, 32, 40, 50, 65, 70, 80, 100, 140, 200, 240``

    An iterable of integers representing the sizes of avatars to generate on upload. This can save rendering time later on if you pre-generate the resized versions.

AWS_ACCESS_KEY_ID
-----------------

    | Default: ``''``
    | Env: ``AWS_ACCESS_KEY_ID``

    This is a `Django storage setting <https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html>`__
    Your Amazon Web Services access key, as a string.

AWS_BUCKET_NAME
---------------

    | Default: ``''``
    | Env: ``S3_BUCKET_NAME``

    The name of the S3 bucket GeoNode will pull static and/or media files from. Set through the environment variable S3_BUCKET_NAME.
    This is a `Django storage setting <https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html>`__

AWS_QUERYSTRING_AUTH
--------------------

    | Default: ``False``

    This is a `Django storage setting <https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html>`__
    Setting AWS_QUERYSTRING_AUTH to False to remove query parameter authentication from generated URLs. This can be useful if your S3 buckets are public.

AWS_S3_BUCKET_DOMAIN
--------------------

    https://github.com/GeoNode/geonode/blob/master/geonode/settings.py#L1661
    AWS_S3_BUCKET_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME

AWS_SECRET_ACCESS_KEY
---------------------

    | Default: ``''``
    | Env: ``AWS_SECRET_ACCESS_KEY``

    This is a `Django storage setting <https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html>`__
    Your Amazon Web Services secret access key, as a string.

AWS_STORAGE_BUCKET_NAME
-----------------------

    | Default: ``''``
    | Env: ``S3_BUCKET_NAME``

    This is a `Django storage setting <https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html>`__
    Your Amazon Web Services storage bucket name, as a string.

B
=

BROKER_HEARTBEAT
----------------

    | Default: ``0``

    Heartbeats are used both by the client and the broker to detect if a connection was closed.
    This is a `Celery setting <https://docs.celeryproject.org/en/latest/userguide/configuration.html#broker-heartbeat>`__.


BROKER_TRANSPORT_OPTIONS
------------------------

    Default::

        {
        'fanout_prefix': True,
        'fanout_patterns': True,
        'socket_timeout': 60,
        'visibility_timeout': 86400
        }

    This is a `Celery setting <https://docs.celeryproject.org/en/latest/userguide/configuration.html#new-lowercase-settings>`__.


C
=

CACHES
------

    A dictionary containing the settings for all caches to be used with Django.
    This is a `Django setting <https://docs.djangoproject.com/en/2.2/ref/settings/#std:setting-CACHES>`__

CACHE_TIME
----------

    | Default: ``0``
    | Env: ``CACHE_TIME``

CASCADE_WORKSPACE
-----------------

    | Default: ``geonode``
    | Env: ``CASCADE_WORKSPACE``


CATALOGUE
---------

    A dict with the following keys:

     ENGINE: The CSW backend (default is ``geonode.catalogue.backends.pycsw_local``)
     URL: The FULLY QUALIFIED base URL to the CSW instance for this GeoNode
     USERNAME: login credentials (if required)
     PASSWORD: login credentials (if required)

    pycsw is the default CSW enabled in GeoNode. pycsw configuration directives
    are managed in the PYCSW entry.

CELERYD_POOL_RESTARTS
---------------------

    Default: ``True``

    This is a `Celery setting <https://docs.celeryproject.org/en/latest/userguide/configuration.html#new-lowercase-settings>`__.

CELERY_ACCEPT_CONTENT
---------------------

    Defaul: ``['json']``

    This is a `Celery setting <https://docs.celeryproject.org/en/latest/userguide/configuration.html#new-lowercase-settings>`__.

CELERY_ACKS_LATE
----------------

    Default: ``True``

    This is a `Celery setting <http://docs.celeryproject.org/en/3.1/configuration.html#celery-acks-late>`__

CELERY_BEAT_SCHEDULE
--------------------

    Here you can define your scheduled task.

CELERY_DISABLE_RATE_LIMITS
--------------------------

    Default: ``False``

    This is a `Celery setting <https://docs.celeryproject.org/en/latest/userguide/configuration.html#new-lowercase-settings>`__.

CELERY_ENABLE_UTC
-----------------

    Default: ``True``

    This is a `Celery setting <https://docs.celeryproject.org/en/latest/userguide/configuration.html#new-lowercase-settings>`__.

CELERY_MAX_CACHED_RESULTS
-------------------------

    Default: ``32768``

    This is a `Celery setting <https://docs.celeryproject.org/en/latest/userguide/configuration.html#new-lowercase-settings>`__.

CELERY_MESSAGE_COMPRESSION
--------------------------

    Default: ``gzip``

    This is a `Celery setting <https://docs.celeryproject.org/en/latest/userguide/configuration.html#new-lowercase-settings>`__.

CELERY_RESULT_PERSISTENT
------------------------

    Default: ``False``

    This is a `Celery setting <https://docs.celeryproject.org/en/latest/userguide/configuration.html#new-lowercase-settings>`__.

CELERY_RESULT_SERIALIZER
------------------------

    Default: ``json``

    This is a `Celery setting <https://docs.celeryproject.org/en/latest/userguide/configuration.html#new-lowercase-settings>`__.

CELERY_SEND_TASK_SENT_EVENT
---------------------------

    Default: ``True``

    If enabled, a task-sent event will be sent for every task so tasks can be tracked before they are consumed by a worker. This is a `Celery setting <https://docs.celeryproject.org/en/latest/userguide/configuration.html#new-lowercase-settings>`__.


CELERY_TASK_ALWAYS_EAGER
------------------------

    Default: ``False if ASYNC_SIGNALS else True``

    This is a `Celery setting <https://docs.celeryproject.org/en/latest/userguide/configuration.html#new-lowercase-settings>`__.

CELERY_TASK_CREATE_MISSING_QUEUES
---------------------------------

    Default: ``True``

    This is a `Celery setting <https://docs.celeryproject.org/en/latest/userguide/configuration.html#new-lowercase-settings>`__.

CELERY_TASK_IGNORE_RESULT
-------------------------

    Default: ``True``

    This is a `Celery setting <https://docs.celeryproject.org/en/latest/userguide/configuration.html#new-lowercase-settings>`__.

CELERY_TASK_QUEUES
------------------

    Default::

        Queue('default', GEONODE_EXCHANGE, routing_key='default'),
        Queue('geonode', GEONODE_EXCHANGE, routing_key='geonode'),
        Queue('update', GEONODE_EXCHANGE, routing_key='update'),
        Queue('cleanup', GEONODE_EXCHANGE, routing_key='cleanup'),
        Queue('email', GEONODE_EXCHANGE, routing_key='email'),

    A tuple with registered Queues.

CELERY_TASK_RESULT_EXPIRES
--------------------------

    Default: ``43200``

    This is a `Celery setting <https://docs.celeryproject.org/en/latest/userguide/configuration.html#new-lowercase-settings>`__.

CELERY_TASK_SERIALIZER
----------------------

    Default: ``json``

    This is a `Celery setting <https://docs.celeryproject.org/en/latest/userguide/configuration.html#new-lowercase-settings>`__.

CELERY_TIMEZONE
---------------

    | Default: ``UTC``
    | Env: ``TIME_ZONE``

    This is a `Celery setting <https://docs.celeryproject.org/en/latest/userguide/configuration.html#new-lowercase-settings>`__.

CELERY_TRACK_STARTED
--------------------

    Default: ``True``

    This is a `Celery setting <https://docs.celeryproject.org/en/latest/userguide/configuration.html#new-lowercase-settings>`__.

CELERY_WORKER_DISABLE_RATE_LIMITS
---------------------------------

    Default: ``False``

    Disable the worker rate limits (number of tasks that can be run in a given time frame).

CELERY_WORKER_SEND_TASK_EVENTS
------------------------------

    Default: ``False``

    Send events so the worker can be monitored by other tools.

CLIENT_RESULTS_LIMIT
--------------------

    | Default: ``20``
    | Env: ``CLIENT_RESULTS_LIMIT``

    The Number of results per page listed in the GeoNode search pages. Different from ``API_LIMIT_PER_PAGE``, affecting the number of items returned by the APIs.

CREATE_LAYER
------------

    Default: ``False``

    Enable the create layer plugin.

CKAN_ORIGINS
------------

    Default::

        CKAN_ORIGINS = [{
            "label":"Humanitarian Data Exchange (HDX)",
            "url":"https://data.hdx.rwlabs.org/dataset/new?title={name}&notes={abstract}",
            "css_class":"hdx"
        }]

    A list of dictionaries that are used to generate the links to CKAN instances displayed in the Share tab.  For each origin, the name and abstract format parameters are replaced by the actual values of the ResourceBase object (layer, map, document).  This is not enabled by default.  To enable, uncomment the following line: SOCIAL_ORIGINS.extend(CKAN_ORIGINS).

CSRF_COOKIE_HTTPONLY
--------------------

    | Default: `False`
    | Env: `CSRF_COOKIE_HTTPONLY`

    Whether to use HttpOnly flag on the CSRF cookie. If this is set to True, client-side JavaScript will not be able to access the CSRF cookie. This is a `Django Setting <https://docs.djangoproject.com/en/2.1/ref/settings/#csrf-cookie-httponly>`__

CSRF_COOKIE_SECURE
------------------

    | Default: `False`
    | Env: `CSRF_COOKIE_HTTPONLY`

    Whether to use a secure cookie for the CSRF cookie. If this is set to True, the cookie will be marked as “secure,” which means browsers may ensure that the cookie is only sent with an HTTPS connection. This is a `Django Setting <https://docs.djangoproject.com/en/2.1/ref/settings/#csrf-cookie-secure>`__

D
=

DATA_UPLOAD_MAX_NUMBER_FIELDS
-----------------------------

    Default: `100000`

    Maximum value of parsed attributes.

DEBUG
-----

    Default: `False`

    One of the main features of debug mode is the display of detailed error pages. If your app raises an exception when DEBUG is True, Django will display a detailed traceback, including a lot of metadata about your environment, such as all the currently defined Django settings (from settings.py).
    This is a `Django Setting <https://docs.djangoproject.com/en/2.1/ref/settings/#debug>`__


DEBUG_STATIC
------------

    Default: `False`

    Load non minified version of static files.

DEFAULT_ANONYMOUS_DOWNLOAD_PERMISSION
-------------------------------------

    Default: `True`

    Whether the uploaded resources should downloadable by default.

DEFAULT_ANONYMOUS_VIEW_PERMISSION
---------------------------------

    Default: `True`

    Whether the uploaded resources should be public by default.

DEFAULT_LAYER_FORMAT
--------------------

    | Default: `image/png`
    | Env: `DEFAULT_LAYER_FORMAT`

    The default format for requested tile images.


DEFAULT_MAP_CENTER
------------------

    | Default: ``(0, 0)``
    | Env: ``DEFAULT_MAP_CENTER_X`` ``DEFAULT_MAP_CENTER_Y``

    A 2-tuple with the latitude/longitude coordinates of the center-point to use
    in newly created maps.

DEFAULT_MAP_CRS
---------------

    | Default: ``EPSG:3857``
    | Env: ``DEFAULT_MAP_CRS``

    The default map projection. Default: EPSG:3857

DEFAULT_MAP_ZOOM
----------------

    | Default: ``0``
    | Env: ``DEFAULT_MAP_ZOOM``

    The zoom-level to use in newly created maps.  This works like the OpenLayers
    zoom level setting; 0 is at the world extent and each additional level cuts
    the viewport in half in each direction.

DEFAULT_SEARCH_SIZE
-------------------

    | Default: ``10``
    | Env: ``DEFAULT_SEARCH_SIZE``

    An integer that specifies the default search size when using ``geonode.search`` for querying data.

DEFAULT_WORKSPACE
-----------------

    | Default: ``geonode``
    | Env: ``DEFAULT_WORKSPACE``

    The standard GeoServer workspace.

DELAYED_SECURITY_INTERVAL
-------------------------

    | Default: ``60``
    | Env: ``DELAYED_SECURITY_INTERVAL``

    This setting only works when ``DELAYED_SECURITY_SIGNALS`` has been activated and the Celery worker is running.
    It defines the time interval in seconds for the Celery task to check if there are resources to be synchronized.

    For more details see ``DELAYED_SECURITY_SIGNALS``

DELAYED_SECURITY_SIGNALS
------------------------

    | Default: ``False``
    | Env: ``DELAYED_SECURITY_SIGNALS``

    This setting only works when ``GEOFENCE_SECURITY_ENABLED`` has been set to ``True`` and GeoNode is making use of the ``GeoServer BACKEND``.

    By setting this to ``True``, every time the permissions will be updated/changed for a Layer, they won't be applied immediately but only and only if
    either:

    a. A Celery Worker is running and it is able to execute the ``geonode.security.tasks.synch_guardian`` periodic task;
       notice that the task will be executed every ``DELAYED_SECURITY_INTERVAL`` seconds.

    b. A periodic ``cron`` job runs the ``sync_security_rules`` management command, or either it is manually executed from the Django shell.

    c. The user, owner of the Layer or with rights to change its permissions, clicks on the GeoNode UI button ``Sync permissions immediately``

    .. warning:: Layers won't be accessible to public users anymore until the Security Rules are not synchronized!

DISPLAY_COMMENTS
----------------

    | Default: ``True``
    | Env: ``DISPLAY_COMMENTS``

    If set to False comments are hidden.


DISPLAY_RATINGS
---------------

    | Default: ``True``
    | Env: ``DISPLAY_RATINGS``

    If set to False ratings are hidden.

DISPLAY_SOCIAL
--------------

    | Default: ``True``
    | Env: ``DISPLAY_SOCIAL``

    If set to False social sharing is hidden.

DISPLAY_WMS_LINKS
-----------------

    | Default: ``True``
    | Env: ``DISPLAY_WMS_LINKS``

    If set to False direct WMS link to GeoServer is hidden.

DISPLAY_ORIGINAL_DATASET_LINK
-----------------------------

    | Default: ``True``
    | Env: ``DISPLAY_ORIGINAL_DATASET_LINK``

    If set to False original dataset download is hidden.

DOWNLOAD_FORMATS_METADATA
-------------------------

    Specifies which metadata formats are available for users to download.

    Default::

        DOWNLOAD_FORMATS_METADATA = [
            'Atom', 'DIF', 'Dublin Core', 'ebRIM', 'FGDC', 'ISO',
        ]

DOWNLOAD_FORMATS_VECTOR
-----------------------

    Specifies which formats for vector data are available for users to download.

    Default::

        DOWNLOAD_FORMATS_VECTOR = [
            'JPEG', 'PDF', 'PNG', 'Zipped Shapefile', 'GML 2.0', 'GML 3.1.1', 'CSV',
            'Excel', 'GeoJSON', 'KML', 'View in Google Earth', 'Tiles',
        ]

DOWNLOAD_FORMATS_RASTER
-----------------------

    Specifies which formats for raster data are available for users to download.

    Default::

        DOWNLOAD_FORMATS_RASTER = [
            'JPEG', 'PDF', 'PNG' 'Tiles',
        ]

E
=

EMAIL_ENABLE
------------

    Default: ``False``

    Options:

        * EMAIL_BACKEND

            Default: ``django.core.mail.backends.smtp.EmailBackend``

            Env: ``DJANGO_EMAIL_BACKEND``

        * EMAIL_HOST

            Default: ``localhost``

        * EMAIL_PORT

            Default: ``25``

        * EMAIL_HOST_USER

            Default: ``''``

        * EMAIL_HOST_PASSWORD

            Default: ``''``

        * EMAIL_USE_TLS

            Default: ``False``

        * DEFAULT_FROM_EMAIL

            Default: ``GeoNode <no-reply@geonode.org>``

F
=

FREETEXT_KEYWORDS_READONLY
--------------------------

    | Default: ``False``
    | Env: ``FREETEXT_KEYWORDS_READONLY``

    Make Free-Text Keywords writable from users. Or read-only when set to False.

G
=

GEOFENCE_SECURITY_ENABLED
-------------------------

    | Default: ``True`` (False is Test is true)
    | Env: ``GEOFENCE_SECURITY_ENABLED``

    Whether the geofence security system is used.

GEOIP_PATH
----------

    | Default: ``Path to project``
    | Env: ``PROJECT_ROOT``

    The local path where GeoIPCities.dat is written to. Make sure your user has to have write permissions.


GEONODE_APPS
------------

    If enabled contrib apps are used.

GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY
------------------------------------

    Default:  ``"mapstore"``

    The library to use for display preview images of layers.  The library choices are:

     ``"leaflet"``
     ``"geoext"``

GEONODE_EXCHANGE
----------------

    Default:: ``Exchange("default", type="direct", durable=True)``

    The definition of Exchanges published by geonode. Find more about Exchanges at `celery docs <https://docs.celeryproject.org/en/latest/userguide/routing.html#exchanges-queues-and-routing-keys>`__.


GEOSERVER_EXCHANGE
------------------

    Default:: ``Exchange("geonode", type="topic", durable=False)``

    The definition of Exchanges published by GeoServer. Find more about Exchanges at `celery docs <https://docs.celeryproject.org/en/latest/userguide/routing.html#exchanges-queues-and-routing-keys>`__.

GEOSERVER_LOCATION
------------------

    | Default: ``http://localhost:8080/geoserver/``
    | Env: ``GEOSERVER_LOCATION``

    Url under which GeoServer is available.

GEOSERVER_PUBLIC_HOST
---------------------

    | Default: ``SITE_HOST_NAME`` (Variable)
    | Env: ``GEOSERVER_PUBLIC_HOST``

    Public hostname under which GeoServer is available.

GEOSERVER_PUBLIC_LOCATION
-------------------------

    | Default: ``SITE_HOST_NAME`` (Variable)
    | Env: ``GEOSERVER_PUBLIC_LOCATION``

    Public location under which GeoServer is available.

GEOSERVER_PUBLIC_PORT
---------------------

    | Default: ``8080 (Variable)``
    | Env: ``GEOSERVER_PUBLIC_PORT``


    Public Port under which GeoServer is available.

GEOSERVER_WEB_UI_LOCATION
-------------------------

    | Default: ``GEOSERVER_PUBLIC_LOCATION (Variable)``
    | Env: ``GEOSERVER_WEB_UI_LOCATION``

    Public location under which GeoServer is available.

GROUP_PRIVATE_RESOURCES
-----------------------

    | Default: ``False``
    | Env: ``GROUP_PRIVATE_RESOURCES``

    If this option is enabled, Resources belonging to a Group won't be visible by others

H
=

HAYSTACK_FACET_COUNTS
---------------------

    | Default: ``True``
    | Env: ``HAYSTACK_FACET_COUNTS``

    If set to True users will be presented with feedback about the number of resources which matches terms they may be interested in.

HAYSTACK_SEARCH
---------------

    | Default: ``False``
    | Env: ``HAYSTACK_SEARCH``

    Enable/disable haystack Search Backend Configuration.


L
=

LEAFLET_CONFIG
--------------

    A dictionary used for Leaflet configuration.

LICENSES
--------

    Default::

        {
            'ENABLED': True,
            'DETAIL': 'above',
            'METADATA': 'verbose',
        }

    Enable Licenses User Interface

LOCAL_SIGNALS_BROKER_URL
------------------------

    Default: ``memory://``

LOCKDOWN_GEONODE
----------------

    | Default: ``False``
    | Env: ``LOCKDOWN_GEONODE``

    By default, the GeoNode application allows visitors to view most pages without being authenticated. If this is set to ``True``
    users must be authenticated before accessing URL routes not included in ``AUTH_EXEMPT_URLS``.

LOGIN_URL
---------

    | Default: ``{}account/login/'.format(SITEURL)``
    | Env: ``LOGIN_URL``

    The URL where requests are redirected for login.


LOGOUT_URL
----------

    | Default: ``{}account/login/'.format(SITEURL)``
    | Env: ``LOGOUT_URL``

    The URL where requests are redirected for logout.

M
=

MAP_CLIENT_USE_CROSS_ORIGIN_CREDENTIALS
---------------------------------------

    | Default: ``False``
    | Env: ``MAP_CLIENT_USE_CROSS_ORIGIN_CREDENTIALS``

    Enables cross origin requests for geonode-client.

MAX_DOCUMENT_SIZE
-----------------

    | Default:``2``
    | Env: ``MAX_DOCUMENT_SIZE``

    Allowed size for documents in MB.

MISSING_THUMBNAIL
-----------------

    Default: ``geonode/img/missing_thumb.png``

    The path to an image used as thumbnail placeholder.

MODIFY_TOPICCATEGORY
--------------------

    Default: ``False``

    Metadata Topic Categories list should not be modified, as it is strictly defined
    by ISO (See: http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml
    and check the <CodeListDictionary gml:id="MD_MD_TopicCategoryCode"> element).

    Some customization is still possible changing the is_choice and the GeoNode
    description fields.

    In case it is necessary to add/delete/update categories, it is
    possible to set the MODIFY_TOPICCATEGORY setting to True.

MONITORING_ENABLED
------------------

    Default: ``False``

    Enable internal monitoring application (`geonode.monitoring`). If set to `True`, add following code to your local settings:

    .. code::

        MONITORING_ENABLED = True
        # add following lines to your local settings to enable monitoring
        if MONITORING_ENABLED:
            INSTALLED_APPS + ('geonode.monitoring',)
            MIDDLEWARE_CLASSES + ('geonode.monitoring.middleware.MonitoringMiddleware',)

    See :ref:`geonode_monitoring` for details.

.. _monitoring-data-aggregation:

MONITORING_DATA_AGGREGATION
---------------------------

    Default:

    .. code::

        (
            (timedelta(seconds=0), timedelta(minutes=1),),
            (timedelta(days=1), timedelta(minutes=60),),
            (timedelta(days=14), timedelta(days=1),),
        )

    Configure aggregation of past data to control data resolution. It lists data age and aggregation in reverse order, by default:

    | - for current data, 1 minute resolution
    | - for data older than 1 day, 1-hour resolution
    | - for data older than 2 weeks, 1 day resolution

    See :ref:`geonode_monitoring` for further details.

    This setting takes effects only if :ref:`user-analytics` is true.

MONITORING_DATA_TTL
-------------------

    | Default: ``7``
    | Env: ``MONITORING_DATA_TTL``

    How long monitoring data should be stored in days.

MONITORING_DISABLE_CSRF
-----------------------

    | Default: ``False``
    | Env: ``MONITORING_DISABLE_CSRF``

    Set this to true to disable csrf check for notification config views, use with caution - for dev purpose only.

.. _monitoring-skip-paths:

MONITORING_SKIP_PATHS
-----------------------

    Default:

    .. code::

        (
            '/api/o/',
            '/monitoring/',
            '/admin',
            '/lang.js',
            '/jsi18n',
            STATIC_URL,
            MEDIA_URL,
            re.compile('^/[a-z]{2}/admin/'),
        )

    Skip certain useless paths to not to mud analytics stats too much.
    See :ref:`geonode_monitoring` to learn more about it.

    This setting takes effects only if :ref:`user-analytics` is true.

N
=

NOTIFICATIONS_MODULE
--------------------

    Default: ``pinax.notifications``

    App used for notifications. (pinax.notifications or notification)

NOTIFICATION_ENABLED
--------------------

    | Default: ``True``
    | Env: ``NOTIFICATION_ENABLED``

    Enable or disable the notification system.

O
=

OAUTH2_PROVIDER
---------------

    Django OAuth Toolkit provides a support layer for Django REST Framework.
    For settings visit: `OAuth Toolkit settings <https://django-oauth-toolkit.readthedocs.io/en/latest/rest-framework/getting_started.html>`__

OGC_SERVER_DEFAULT_PASSWORD
---------------------------

    | Default: ``geoserver``
    | Env: ``GEOSERVER_ADMIN_PASSWORD``

    The geoserver password.

OGC_SERVER_DEFAULT_USER
-----------------------

    | Default: ``admin``
    | Env: ``GEOSERVER_ADMIN_USER``

    The geoserver user.

OGC_SERVER
----------

    Default: ``{}`` (Empty dictionary)

    A dictionary of OGC servers and their options.  The main
    server should be listed in the 'default' key.  If there is no 'default'
    key or if the ``OGC_SERVER`` setting does not exist, Geonode will raise
    an Improperly Configured exception.  Below is an example of the ``OGC_SERVER``
    setting::

       OGC_SERVER = {
         'default' : {
             'LOCATION' : 'http://localhost:8080/geoserver/',
             'USER' : 'admin',
             'PASSWORD' : 'geoserver',
         }
       }

    * BACKEND

        Default: ``"geonode.geoserver"``

        The OGC server backend to use.  The backend choices are:

         ``'geonode.geoserver'``

    * BACKEND_WRITE_ENABLED

        Default: ``True``

        Specifies whether the OGC server can be written to.  If False, actions that modify
        data on the OGC server will not execute.

    * DATASTORE

        Default: ``''`` (Empty string)

        An optional string that represents the name of a vector datastore, where Geonode uploads are imported into. To support vector datastore imports there also needs to be an
        entry for the datastore in the ``DATABASES`` dictionary with the same name.  Example::

         OGC_SERVER = {
           'default' : {
              'LOCATION' : 'http://localhost:8080/geoserver/',
              'USER' : 'admin',
              'PASSWORD' : 'geoserver',
              'DATASTORE': 'geonode_imports'
           }
         }

         DATABASES = {
          'default': {
              'ENGINE': 'django.db.backends.sqlite3',
              'NAME': 'development.db',
          },
          'geonode_imports' : {
              'ENGINE': 'django.contrib.gis.db.backends.postgis',
              'NAME': 'geonode_imports',
              'USER' : 'geonode_user',
              'PASSWORD' : 'a_password',
              'HOST' : 'localhost',
              'PORT' : '5432',
           }
          }

    * GEONODE_SECURITY_ENABLED

        Default: ``True``

        A boolean that represents whether GeoNode's security application is enabled.

    * LOCATION

        Default: ``"http://localhost:8080/geoserver/"``

        A base URL from which GeoNode can construct OGC service URLs.
        If using GeoServer you can determine this by
        visiting the GeoServer administration home page without the
        /web/ at the end.  For example, if your GeoServer administration app is at
        http://example.com/geoserver/web/, your server's location is http://example.com/geoserver.

    * MAPFISH_PRINT_ENABLED

        Default: ``True``

        A boolean that represents whether the MapFish printing extension is enabled on the server.

    * PASSWORD

        Default: ``'geoserver'``

        The administrative password for the OGC server as a string.

    * PRINT_NG_ENABLED

        Default: ``True``

        A boolean that represents whether printing of maps and layers is enabled.

    * PUBLIC_LOCATION

        Default: ``"http://localhost:8080/geoserver/"``

        The URL used to in most public requests from Geonode.  This setting allows a user to write to one OGC server (the LOCATION setting)
        and read from a separate server or the PUBLIC_LOCATION.

    * USER

        Default: ``'admin'``

        The administrative username for the OGC server as a string.

    * WMST_ENABLED

        Default: ``False``

        Not implemented.

    * WPS_ENABLED

        Default: ``False``

        Not implemented.

    * TIMEOUT

        Default: ``10``

        The maximum time, in seconds, to wait for the server to respond.

OGP_URL
-------

    | Default: ``http://geodata.tufts.edu/solr/select``
    | Env: ``OGP_URL``

    Endpoint of geodata.tufts.edu getCapabilities.

OPENGRAPH_ENABLED
-----------------

    Default:: ``True``

    A boolean that specifies whether Open Graph is enabled.  Open Graph is used by Facebook and Slack.

P
=

PINAX_NOTIFICATIONS_BACKENDS
----------------------------

    Default: ``("email", _EMAIL_BACKEND, 0),``

    Used notification backend. This is a `pinax notification setting: <https://django-notification.readthedocs.io/en/latest/settings.html#pinax-notifications-backends>`__

PINAX_NOTIFICATIONS_LOCK_WAIT_TIMEOUT
-------------------------------------

    | Default: ``-1``
    | Env: ``NOTIFICATIONS_LOCK_WAIT_TIMEOUT``

    It defines how long to wait for the lock to become available. Default of -1 means to never wait for the lock to become available.
    This is a `pinax notification setting: <https://django-notification.readthedocs.io/en/latest/settings.html#pinax-notifications-lock-wait-timeout>`__

PINAX_NOTIFICATIONS_QUEUE_ALL
-----------------------------

    | Default: ``-1``
    | Env: ``NOTIFICATIONS_LOCK_WAIT_TIMEOUT``

    By default, calling notification.send will send the notification immediately, however, if you set this setting to True, then the default behavior of the send method will be to queue messages in the database for sending via the emit_notices command.
    This is a `pinax notification setting: <https://django-notification.readthedocs.io/en/latest/settings.html#pinax-notifications-queue-all>`__

PROXY_ALLOWED_HOSTS
-------------------

    Default: ``()`` (Empty tuple)

    A tuple of strings representing the host/domain names that GeoNode can proxy requests to. This is a security measure
    to prevent an attacker from using the GeoNode proxy to render malicious code or access internal sites.

    Values in this tuple can be fully qualified names (e.g. 'www.geonode.org'), in which case they will be matched against
    the request’s Host header exactly (case-insensitive, not including port). A value beginning with a period can be used
    as a subdomain wildcard: ``.geonode.org`` will match geonode.org, www.geonode.org, and any other subdomain of
    geonode.org. A value of '*' will match anything and is not recommended for production deployments.


PROXY_URL
---------

    Default ``/proxy/?url=``

    The URL to a proxy that will be used when making client-side requests in GeoNode.  By default, the
    internal GeoNode proxy is used but administrators may favor using their own, less restrictive proxies.


PYCSW
-----

  A dict with pycsw's configuration.  Of note are the sections
  ``metadata:main`` to set CSW server metadata and ``metadata:inspire``
  to set INSPIRE options.  Setting ``metadata:inspire['enabled']`` to ``true``
  will enable INSPIRE support.   Server level configurations can be overridden
  in the ``server`` section.  See http://docs.pycsw.org/en/latest/configuration.html
  for full pycsw configuration details.

R
=

RABBITMQ_SIGNALS_BROKER_URL
---------------------------

    Default: ``amqp://localhost:5672``

    The Rabbitmq endpoint

REDIS_SIGNALS_BROKER_URL
------------------------

    Default: ``redis://localhost:6379/0``

    The Redis endpoint.

REGISTRATION_OPEN
-----------------

    Default: ``False``

    A boolean that specifies whether users can self-register for an account on your site.

RESOURCE_PUBLISHING
-------------------

    Default: ``False``

    By default, the GeoNode application allows GeoNode staff members to
    publish/unpublish resources.
    By default, resources are published when created. When this setting is set to
    True the staff members will be able to unpublish a resource (and eventually
    publish it back).

S
=

S3_MEDIA_ENABLED
----------------

    | Default: ``False``
    | Env: ``S3_MEDIA_ENABLED``

    Enable/disable Amazon S3 media storage.

S3_STATIC_ENABLED
-----------------

    | Default: ``False``
    | Env: ``S3_STATIC_ENABLED``

    Enable/disable Amazon S3 static storage.

SEARCH_FILTERS
--------------

    Default::

    'TEXT_ENABLED': True,
    'TYPE_ENABLED': True,
    'CATEGORIES_ENABLED': True,
    'OWNERS_ENABLED': True,
    'KEYWORDS_ENABLED': True,
    'H_KEYWORDS_ENABLED': True,
    'T_KEYWORDS_ENABLED': True,
    'DATE_ENABLED': True,
    'REGION_ENABLED': True,
    'EXTENT_ENABLED': True,

    Enabled Search Filters for filtering resources.

SECURE_BROWSER_XSS_FILTER
-------------------------

    | Default: ``True``
    | Env: ``SECURE_BROWSER_XSS_FILTER``

    If True, the SecurityMiddleware sets the X-XSS-Protection: 1; mode=block header on all responses that do not already have it.
    This is `<Django settings. https://docs.djangoproject.com/en/2.1/ref/settings/#secure-browser-xss-filter>`__

SECURE_CONTENT_TYPE_NOSNIFF
---------------------------

    | Default: ``True``
    | Env: ``SECURE_CONTENT_TYPE_NOSNIFF``

    If True, the SecurityMiddleware sets the X-Content-Type-Options: nosniff header on all responses that do not already have it.
    This is `Django settings: <https://docs.djangoproject.com/en/2.1/ref/settings/#secure-content-type-nosniff>`__


SECURE_HSTS_INCLUDE_SUBDOMAINS
------------------------------

    | Default: ``True``
    | Env: ``SECURE_HSTS_INCLUDE_SUBDOMAINS``

    This is Django settings: https://docs.djangoproject.com/en/2.1/ref/settings/#secure-hsts-include-subdomains

SECURE_HSTS_SECONDS
-------------------

    | Default: ``3600``
    | Env: ``SECURE_HSTS_SECONDS``

    This is `Django settings: <https://docs.djangoproject.com/en/2.1/ref/settings/#secure-hsts-seconds>`__
    If set to a non-zero integer value, the SecurityMiddleware sets the HTTP Strict Transport Security header on all responses that do not already have it.

SECURE_SSL_REDIRECT
-------------------

    If True, the SecurityMiddleware redirects all non-HTTPS requests to HTTPS (except for those URLs matching a regular expression listed in SECURE_REDIRECT_EXEMPT).
    This is `Django settings: <https://docs.djangoproject.com/en/2.1/ref/settings/#secure-ssl-redirect>`__

SERVICE_UPDATE_INTERVAL
-----------------------

    | Default: ``0``

    The Interval services are updated.

SESSION_COOKIE_SECURE
---------------------

    | Default: ``False``
    | Env: ``SESSION_COOKIE_SECURE``

    This is a `Django setting: <https://docs.djangoproject.com/en/2.1/ref/settings/#session-cookie-secure>`__

SESSION_EXPIRED_CONTROL_ENABLED
-------------------------------

    | Default: ``True``
    | Env: ``SESSION_EXPIRED_CONTROL_ENABLED``

    By enabling this variable, a new middleware ``geonode.security.middleware.SessionControlMiddleware`` will be added to the ``MIDDLEWARE_CLASSES``.
    The class will check every request to GeoNode and it will force a log out whenever one of the following conditions occurs:

    #. The OAuth2 Access Token is not valid anymore or it is expired.

       .. warning:: The Access Token might be invalid for various reasons. Usually a misconfiguration of the OAuth2 ``GeoServer`` application.
                    The latter is typically installed and configured automatically at GeoNode bootstrap through the default fixtures.
    #. The user has been deactivated for some reason; an Admin has disabled it or its password has expired.

    Whenever the middleware terminates the session and the user forced to log out, a message will appear to the GeoNode interface.

SHOW_PROFILE_EMAIL
------------------

    Default: ``False``

    A boolean which specifies whether to display the email in the user’s profile.

SITE_HOST_NAME
--------------

    | Default: ``localhost``
    | Env: ``SITE_HOST_NAME``

    The hostname used for GeoNode.

SITE_HOST_PORT
--------------

    | Default: ``8000``
    | Env: ``SITE_HOST_PORT``

    The Site hostport.

SITEURL
-------

    Default: ``'http://localhost:8000/'``

    A base URL for use in creating absolute links to Django views and generating links in metadata.

SKIP_PERMS_FILTER
-----------------

    | Default: ``False``
    | Env: ``SKIP_PERMS_FILTER``

    If set to true permissions prefiltering is avoided.

SOCIALACCOUNT_ADAPTER
---------------------

    Default: ``geonode.people.adapters.SocialAccountAdapter``

    This is a `django-allauth setting <https://django-allauth.readthedocs.io/en/latest/configuration.html#configuration>`__
    It allows specifying a custom class to handle authentication for social accounts.

SOCIALACCOUNT_AUTO_SIGNUP
-------------------------

    Default: ``True``

    Attempt to bypass the signup form by using fields (e.g. username, email) retrieved from the social account provider.
    This is a `Django-allauth setting: <https://django-allauth.readthedocs.io/en/latest/configuration.html>`__


SOCIALACCOUNT_PROVIDERS
-----------------------

  Default::

      {
          'linkedin_oauth2': {
              'SCOPE': [
                  'r_emailaddress',
                  'r_basicprofile',
              ],
              'PROFILE_FIELDS': [
                  'emailAddress',
                  'firstName',
                  'headline',
                  'id',
                  'industry',
                  'lastName',
                  'pictureUrl',
                  'positions',
                  'publicProfileUrl',
                  'location',
                  'specialties',
                  'summary',
              ]
          },
          'facebook': {
              'METHOD': 'oauth2',
              'SCOPE': [
                  'email',
                  'public_profile',
              ],
              'FIELDS': [
                  'id',
                  'email',
                  'name',
                  'first_name',
                  'last_name',
                  'verified',
                  'locale',
                  'timezone',
                  'link',
                  'gender',
              ]
          },
      }

  This is a `django-allauth setting <https://django-allauth.readthedocs.io/en/latest/configuration.html#configuration>`__
  It should be a dictionary with provider specific settings

SOCIALACCOUNT_PROFILE_EXTRACTORS
--------------------------------

  Default::

      {
          "facebook": "geonode.people.profileextractors.FacebookExtractor",
          "linkedin_oauth2": "geonode.people.profileextractors.LinkedInExtractor",
      }

  A dictionary with provider ids as keys and path to custom profile extractor
  classes as values.

SOCIAL_BUTTONS
--------------

    Default: ``True``

    A boolean which specifies whether the social media icons and JavaScript should be rendered in GeoNode.

SOCIAL_ORIGINS
--------------

    Default::

        SOCIAL_ORIGINS = [{
            "label":"Email",
            "url":"mailto:?subject={name}&body={url}",
            "css_class":"email"
        }, {
            "label":"Facebook",
            "url":"http://www.facebook.com/sharer.php?u={url}",
            "css_class":"fb"
        }, {
            "label":"Twitter",
            "url":"https://twitter.com/share?url={url}",
            "css_class":"tw"
        }, {
            "label":"Google +",
            "url":"https://plus.google.com/share?url={url}",
            "css_class":"gp"
        }]

    A list of dictionaries that are used to generate the social links displayed in the Share tab.  For each origin, the name and URL format parameters are replaced by the actual values of the ResourceBase object (layer, map, document).


SRID
----

    Default::

        {
        'DETAIL': 'never',
        }

T
=

TASTYPIE_DEFAULT_FORMATS
------------------------

    Default: ``json``

    This setting allows you to globally configure the list of allowed serialization formats for your entire site.
    This is a `tastypie setting: <https://django-tastypie.readthedocs.io/en/v0.9.14/settings.html#tastypie-default-formats>`__

THEME_ACCOUNT_CONTACT_EMAIL
---------------------------

    Default: ``'admin@example.com'``

    This email address is added to the bottom of the password reset page in case users have trouble unlocking their account.

THESAURI
--------

    Default = ``[]``

    A list of Keywords thesauri settings:
    For example `THESAURI = [{'name':'inspire_themes', 'required':True, 'filter':True}, {'name':'inspire_concepts', 'filter':True}, ]`

TOPICCATEGORY_MANDATORY
-----------------------

    | Default: ``False``
    | Env: ``TOPICCATEGORY_MANDATORY``

    If this option is enabled, Topic Categories will become strictly Mandatory on Metadata Wizard

TWITTER_CARD
------------

    Default:: ``True``

    A boolean that specifies whether Twitter cards are enabled.

TWITTER_SITE
------------

    Default:: ``'@GeoNode'``

    A string that specifies the site to for the twitter:site meta tag for Twitter Cards.

TWITTER_HASHTAGS
----------------

    Default:: ``['geonode']``

    A list that specifies the hashtags to use when sharing a resource when clicking on a social link.

U
=

UNOCONV_ENABLE
--------------

    | Default: ``False``
    | Env: ``UNOCONV_ENABLE``

UPLOADER
--------

    Default::

        {
            'BACKEND' : 'geonode.rest',
            'OPTIONS' : {
                'TIME_ENABLED': False,
            }
        }

    A dictionary of Uploader settings and their values.

    * BACKEND

        Default: ``'geonode.rest'``

        The uploader backend to use.  The backend choices are:

         ``'geonode.importer'``
         ``'geonode.rest'``

        The importer backend requires the GeoServer importer extension to be enabled.

    * OPTIONS

        Default::

            'OPTIONS' : {
                'TIME_ENABLED': False,
            }

        * TIME_ENABLED

            Default: ``False``

            A boolean that specifies whether the upload should allow the user to enable time support when uploading data.

USER_MESSAGES_ALLOW_MULTIPLE_RECIPIENTS
---------------------------------------

    | Default: ``True``
    | Env: ``USER_MESSAGES_ALLOW_MULTIPLE_RECIPIENTS``

    Set to true to have multiple recipients in /message/create/

.. _user-analytics:

USER_ANALYTICS_ENABLED
----------------------

    | Default: ``False``
    | Env: ``USER_ANALYTICS_ENABLED``

    Set to true to anonymously collect user data for analytics.
    If true you have to set :ref:`monitoring-data-aggregation` and :ref:`monitoring-skip-paths`.

    See :ref:`geonode_monitoring` to learn more about it.

X
=

X_FRAME_OPTIONS
---------------

Default: ``'ALLOW-FROM %s' % SITEURL``

This is a `Django setting <https://docs.djangoproject.com/en/2.2/ref/clickjacking/#setting-x-frame-options-for-all-responses>`__
