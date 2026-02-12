# Settings

Here’s a list of settings available in GeoNode and their default values.  This includes settings for some external applications that
GeoNode depends on.

For most of them, default values are good. Those should be changed only for advanced configurations in production or heavily hardened systems.

The most common ones can be set through ``environment`` variables to avoid touching the ``settings.py`` file at all.
This is a good practice and also the preferred one to configure GeoNode (and Django apps in general).
Whenever you need to change them, set the environment variable accordingly (where it is available) instead of overriding it through the ``local_settings``.


## A

ACCESS_TOKEN_EXPIRE_SECONDS


    | Default: ``86400``
    | Env: ``ACCESS_TOKEN_EXPIRE_SECONDS``

    When a user logs into GeoNode, if no ``ACCESS_TOKEN`` exists, a new one will be created with a default expiration time of ``ACCESS_TOKEN_EXPIRE_SECONDS`` seconds (1 day by default).

ACCOUNT_ADAPTER


    | Default: ``geonode.people.adapters.LocalAccountAdapter``

    Custom GeoNode People (Users) Account Adapter.

ACCOUNT_APPROVAL_REQUIRED


    | Default: ``False``
    | Env: ``ACCOUNT_APPROVAL_REQUIRED``

    If ``ACCOUNT_APPROVAL_REQUIRED`` equals ``True``, newly registered users must be activated by a superuser through the Admin gui, before they can access GeoNode.

ACCOUNT_CONFIRM_EMAIL_ON_GET


    | Default: ``True``

    This is a `django-allauth setting <https://django-allauth.readthedocs.io/en/latest/configuration.html#configuration>`__
    It allows specifying the HTTP method used when confirming e-mail addresses.

ACCOUNT_EMAIL_REQUIRED


    | Default: ``True``

    This is a `django-allauth setting <https://django-allauth.readthedocs.io/en/latest/configuration.html#configuration>`__
    which controls whether the user is required to provide an e-mail address upon registration.

ACCOUNT_EMAIL_VERIFICATION


    | Default: ``optional``

    This is a `django-allauth setting <https://django-allauth.readthedocs.io/en/latest/configuration.html#configuration>`__

ACCOUNT_LOGIN_REDIRECT_URL


    | Default: ``SITEURL``
    | Env: ``LOGIN_REDIRECT_URL``

    This is a `django-user-accounts setting <https://django-user-accounts.readthedocs.io/en/latest/settings.html>`__
    It allows specifying the default redirect URL after a successful login.

ACCOUNT_LOGOUT_REDIRECT_URL


    | Default: ``SITEURL``
    | Env: ``LOGOUT_REDIRECT_URL``

    This is a `django-user-accounts setting <https://django-user-accounts.readthedocs.io/en/latest/settings.html>`__
    It allows specifying the default redirect URL after a successful logout.

ACCOUNT_NOTIFY_ON_PASSWORD_CHANGE


    | Default: ``True``
    | Env: ``ACCOUNT_NOTIFY_ON_PASSWORD_CHANGE``

    This is a `django-user-accounts setting <https://django-user-accounts.readthedocs.io/en/latest/settings.html>`__

ACCOUNT_OPEN_SIGNUP


    | Default: ``True``
    | Env: ``ACCOUNT_OPEN_SIGNUP``

    This is a `django-user-accounts setting <https://django-user-accounts.readthedocs.io/en/latest/settings.html>`__
    Whether or not people are allowed to self-register to GeoNode or not.

ACCOUNT_SIGNUP_FORM_CLASS


    | Default: ``geonode.people.forms.AllauthReCaptchaSignupForm``
    | Env: ``ACCOUNT_SIGNUP_FORM_CLASS``

    Enabled only when the :ref:`recaptcha_enabled` option is ``True``.

    Ref. to :ref:`recaptcha_enabled`

ACTSTREAM_SETTINGS


    Default::

        {
        'FETCH_RELATIONS': True,
        'USE_PREFETCH': False,
        'USE_JSONFIELD': True,
        'GFK_FETCH_DEPTH': 1,
        }

    Actstream Settings.


ADDITIONAL_DATASET_FILE_TYPES


External application can define additional supported file type other than the default one declared in the `SUPPORTED_DATASET_FILE_TYPES` .

The variable should be declared in this way in `settings.py` (or via application hook):


    .. code::
        ADDITIONAL_DATASET_FILE_TYPES=[
            {
                "id": "dummy_type",
                "label": "Dummy Type",
                "format": "dummy",
                "ext": ["dummy"]
            },
        ]

Please rely on geonode.tests.test_utils.TestSupportedTypes for an example

ADMIN_IP_WHITELIST


    | Default: ``[]``

    When this list is popuplated with a list of IPs or IP ranges (e.g. 192.168.1.0/24) requests from and admin user will be allowe only from IPs matching with the list.

ADMIN_MODERATE_UPLOADS


    | Default: ``False``

    When this variable is set to ``True``, every uploaded resource must be approved before becoming visible to the public users.

    Until a resource is in ``PENDING APPROVAL`` state, only the superusers, owner and group members can access it, unless specific edit permissions have been set for other users or groups.

    A ``Group Manager`` *can* approve the resource, but he cannot publish it whenever the setting ``RESOURCE_PUBLISHING`` is set to ``True``.
    Otherwise, if ``RESOURCE_PUBLISHING`` is set to ``False``, the resource becomes accessible as soon as it is approved.

ADMINS_ONLY_NOTICE_TYPES


    | Default: ``['monitoring_alert',]``

    A list of notification labels that standard users should not either see or set.

    Such notifications will be hidden from the notify settings page and automatically set to false for non-superusers.


ADVANCED_EDIT_EXCLUDE_FIELD

    | Default: ``[]``

    A list of element (item name) to exclude from the Advanced Edit page.

    Example:
    
    ``ADVANCED_EDIT_EXCLUDE_FIELD=['title', 'keywords', 'tkeywords']``


AGON_RATINGS_CATEGORY_CHOICES


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


    Default::

        ['doc', 'docx', 'gif', 'jpg', 'jpeg', 'ods', 'odt', 'odp', 'pdf', 'png',
        'ppt', 'pptx', 'rar', 'sld', 'tif', 'tiff', 'txt', 'xls', 'xlsx', 'xml',
        'zip', 'gz', 'qml']

    A list of acceptable file extensions that can be uploaded to the Documents app.

ANONYMOUS_USER_ID


    | Default: ``-1``
    | Env: ``ANONYMOUS_USER_ID``

    The id of an anonymous user. This is an django-guardian setting.

API_INCLUDE_REGIONS_COUNT


    | Default: ``False``
    | Env: ``API_INCLUDE_REGIONS_COUNT``

    If set to ``True``, a counter with the total number of available regions will be added to the API JSON Serializer.

API_LIMIT_PER_PAGE


    | Default: ``200``
    | Env: ``API_LIMIT_PER_PAGE``

    The Number of items returned by the APIs 0 equals no limit. Different from ``CLIENT_RESULTS_LIMIT``, affecting the number of items per page in the resource list.

API_LOCKDOWN


    | Default: ``True``
    | Env: ``API_LOCKDOWN``

    If this is set to ``True`` users must be authenticated to get search results when search for for users, groups, categories, regions, tags etc.
    Filtering search results of Resourcebase-objects like Layers, Maps or Documents by one of the above types does not work.
    Attention: If API_LOCKDOWN is set to ``False`` all details can be accessed by anonymous users.

ASYNC_SIGNALS


    | Default: ``False``
    | Env: ``ACCOUNT_NOTIFY_ON_PASSWORD_CHANGE``

AUTH_EXEMPT_URLS


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

AUTO_ASSIGN_REGISTERED_MEMBERS_TO_CONTRIBUTORS


    | Default: ``True``
    | Env: ``AUTO_ASSIGN_REGISTERED_MEMBERS_TO_CONTRIBUTORS``

    Assign **new** registered users to the contributors group. If set to `False` new registered members will not obtain automatic permissions to create and edit resources.

AUTO_ASSIGN_REGISTERED_MEMBERS_TO_REGISTERED_MEMBERS_GROUP_NAME


    | Default: ``True``
    | Env: ``AUTO_ASSIGN_REGISTERED_MEMBERS_TO_REGISTERED_MEMBERS_GROUP_NAME``

    Auto assign users to a default ``REGISTERED_MEMBERS_GROUP_NAME`` private group after ``AUTO_ASSIGN_REGISTERED_MEMBERS_TO_REGISTERED_MEMBERS_GROUP_AT``.

AUTO_ASSIGN_REGISTERED_MEMBERS_TO_REGISTERED_MEMBERS_GROUP_AT


    | Default: ``activation``
    | Env: ``AUTO_ASSIGN_REGISTERED_MEMBERS_TO_REGISTERED_MEMBERS_GROUP_AT``
    | Options: ``"registration" | "activation" | "login"``

    Auto assign users to a default ``REGISTERED_MEMBERS_GROUP_NAME`` private group after {"registration" | "activation" | "login"}.

    Notice that whenever ``ACCOUNT_EMAIL_VERIFICATION == True`` and ``ACCOUNT_APPROVAL_REQUIRED == False``, users will be able to register and they became ``active`` already, even if they won't be able to login until the email has been verified.

AUTO_GENERATE_AVATAR_SIZES


    | Default: ``20, 30, 32, 40, 50, 65, 70, 80, 100, 140, 200, 240``

    An iterable of integers representing the sizes of avatars to generate on upload. This can save rendering time later on if you pre-generate the resized versions.

AVATAR_GRAVATAR_SSL


  | Default: ``False``
  | Env: ``AVATAR_GRAVATAR_SSL``
  | Options: ``True | False``

  Force SSL when loading fallback image from gravatar.com.

AVATAR_DEFAULT_URL


  | Default: ``/geonode/img/avatar.png``
  | Env: ``AVATAR_GRAVATAR_SSL``
  | Options: ``"filepath to image"``

  Allows to set a custom fallback image in case a User has not uploaded a profile image.
  Needs ``AVATAR_PROVIDERS`` to be set correctly.

AVATAR_PROVIDERS


  | Default:
  .. code-block::

    'avatar.providers.PrimaryAvatarProvider','avatar.providers.GravatarAvatarProvider','avatar.providers.DefaultAvatarProvider'


  | Env: ``AVATAR_PROVIDERS``
  | Options: ``Avatar provider object``


  This setting configures in which order gravatar images are loaded. A common use case is the use of a local image over a fallback image loaded from gravatar.com.
  To do so you would change the order like:

  .. code-block::

    'avatar.providers.PrimaryAvatarProvider','avatar.providers.DefaultAvatarProvider','avatar.providers.GravatarAvatarProvider'

  (DefaultAvatarProvider before GravatarAvatarProvider)


## B

BING_API_KEY


    | Default: ``None``
    | Env: ``BING_API_KEY``

    This property allows to enable a Bing Aerial background.

    If using ``mapstore`` client library, make sure the ``MAPSTORE_BASELAYERS`` include the following:

    .. code-block:: python

        if BING_API_KEY:
            BASEMAP = {
                "type": "bing",
                "title": "Bing Aerial",
                "name": "AerialWithLabels",
                "source": "bing",
                "group": "background",
                "apiKey": "{{apiKey}}",
                "visibility": False
            }
            DEFAULT_MS2_BACKGROUNDS = [BASEMAP,] + DEFAULT_MS2_BACKGROUNDS


BROKER_HEARTBEAT


    | Default: ``0``

    Heartbeats are used both by the client and the broker to detect if a connection was closed.
    This is a `Celery setting <https://docs.celeryproject.org/en/latest/userguide/configuration.html#broker-heartbeat>`__.


BROKER_TRANSPORT_OPTIONS


    Default::

        {
        'fanout_prefix': True,
        'fanout_patterns': True,
        'socket_timeout': 60,
        'visibility_timeout': 86400
        }

    This is a `Celery setting <https://docs.celeryproject.org/en/latest/userguide/configuration.html#new-lowercase-settings>`__.


## C

CACHES


    Default::

        CACHES = {
            'default': {
                'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
            },
            'resources': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                'TIMEOUT': 600,
                'OPTIONS': {
                    'MAX_ENTRIES': 10000
                }
            }
        }

    A dictionary containing the settings for all caches to be used with Django.
    This is a `Django setting <https://docs.djangoproject.com/en/3.2/ref/settings/#std:setting-CACHES>`__

    The ``'default'`` cache is disabled because we don't have a mechanism to discriminate between client sessions right now, and we don't want all users fetch the same api results.

    The ``'resources'`` is not currently used. It might be helpful for `caching Django template fragments <https://docs.djangoproject.com/en/3.2/topics/cache/#template-fragment-caching>`__ and/or `Tastypie API Caching <https://django-tastypie.readthedocs.io/en/latest/caching.html>`__.


CACHE_BUSTING_STATIC_ENABLED


    | Default: ``False``
    | Env: ``CACHE_BUSTING_STATIC_ENABLED``

    This is a `Django Compressed Manifet storage provided by WhiteNoise <http://whitenoise.evans.io/en/stable/django.html#add-compression-and-caching-support>`__
    A boolean allowing you to enable the ``WhiteNoise CompressedManifestStaticFilesStorage storage``. This works only on a production system.

    .. warning:: This works only if ``DEBUG = False``


CASCADE_WORKSPACE


    | Default: ``geonode``
    | Env: ``CASCADE_WORKSPACE``


CATALOGUE


    A dict with the following keys:

     ENGINE: The CSW backend (default is ``geonode.catalogue.backends.pycsw_local``)
     URL: The FULLY QUALIFIED base URL to the CSW instance for this GeoNode
     USERNAME: login credentials (if required)
     PASSWORD: login credentials (if required)

    pycsw is the default CSW enabled in GeoNode. pycsw configuration directives
    are managed in the PYCSW entry.

CATALOGUE_METADATA_TEMPLATE


    Default : ``catalogue/full_metadata.xml``

    A string with the catalogue xml file needed for the metadata.

CATALOGUE_METADATA_XSL


    Default : ``'/static/metadataxsl/metadata.xsl``

    A string pointing to the XSL used to transform the metadata XML into human readable HTML.

CELERYD_POOL_RESTARTS


    Default: ``True``

    This is a `Celery setting <https://docs.celeryproject.org/en/latest/userguide/configuration.html#new-lowercase-settings>`__.

CELERY_ACCEPT_CONTENT


    Defaul: ``['json']``

    This is a `Celery setting <https://docs.celeryproject.org/en/latest/userguide/configuration.html#new-lowercase-settings>`__.

CELERY_ACKS_LATE


    Default: ``True``

    This is a `Celery setting <http://docs.celeryproject.org/en/3.1/configuration.html#celery-acks-late>`__

CELERY_BEAT_SCHEDULE


    Here you can define your scheduled task.

CELERY_DISABLE_RATE_LIMITS


    Default: ``False``

    This is a `Celery setting <https://docs.celeryproject.org/en/latest/userguide/configuration.html#new-lowercase-settings>`__.

CELERY_ENABLE_UTC


    Default: ``True``

    This is a `Celery setting <https://docs.celeryproject.org/en/latest/userguide/configuration.html#new-lowercase-settings>`__.

CELERY_MAX_CACHED_RESULTS


    Default: ``32768``

    This is a `Celery setting <https://docs.celeryproject.org/en/latest/userguide/configuration.html#new-lowercase-settings>`__.

CELERY_MESSAGE_COMPRESSION


    Default: ``gzip``

    This is a `Celery setting <https://docs.celeryproject.org/en/latest/userguide/configuration.html#new-lowercase-settings>`__.

CELERY_RESULT_PERSISTENT


    Default: ``False``

    This is a `Celery setting <https://docs.celeryproject.org/en/latest/userguide/configuration.html#new-lowercase-settings>`__.

CELERY_RESULT_SERIALIZER


    Default: ``json``

    This is a `Celery setting <https://docs.celeryproject.org/en/latest/userguide/configuration.html#new-lowercase-settings>`__.

CELERY_SEND_TASK_SENT_EVENT


    Default: ``True``

    If enabled, a task-sent event will be sent for every task so tasks can be tracked before they are consumed by a worker. This is a `Celery setting <https://docs.celeryproject.org/en/latest/userguide/configuration.html#new-lowercase-settings>`__.


CELERY_TASK_ALWAYS_EAGER


    Default: ``False if ASYNC_SIGNALS else True``

    This is a `Celery setting <https://docs.celeryproject.org/en/latest/userguide/configuration.html#new-lowercase-settings>`__.

CELERY_TASK_CREATE_MISSING_QUEUES


    Default: ``True``

    This is a `Celery setting <https://docs.celeryproject.org/en/latest/userguide/configuration.html#new-lowercase-settings>`__.

CELERY_TASK_IGNORE_RESULT


    Default: ``True``

    This is a `Celery setting <https://docs.celeryproject.org/en/latest/userguide/configuration.html#new-lowercase-settings>`__.

CELERY_TASK_QUEUES


    Default::

        Queue('default', GEONODE_EXCHANGE, routing_key='default'),
        Queue('geonode', GEONODE_EXCHANGE, routing_key='geonode'),
        Queue('update', GEONODE_EXCHANGE, routing_key='update'),
        Queue('cleanup', GEONODE_EXCHANGE, routing_key='cleanup'),
        Queue('email', GEONODE_EXCHANGE, routing_key='email'),

    A tuple with registered Queues.

CELERY_TASK_RESULT_EXPIRES


    | Default: ``43200``
    | Env: ``CELERY_TASK_RESULT_EXPIRES``

    This is a `Celery setting <https://docs.celeryproject.org/en/latest/userguide/configuration.html#new-lowercase-settings>`__.

CELERY_TASK_SERIALIZER


    Default: ``json``
    Env: ``CELERY_TASK_SERIALIZER``

    This is a `Celery setting <https://docs.celeryproject.org/en/latest/userguide/configuration.html#new-lowercase-settings>`__.

CELERY_TIMEZONE


    | Default: ``UTC``
    | Env: ``TIME_ZONE``

    This is a `Celery setting <https://docs.celeryproject.org/en/latest/userguide/configuration.html#new-lowercase-settings>`__.

CELERY_TRACK_STARTED


    Default: ``True``

    This is a `Celery setting <https://docs.celeryproject.org/en/latest/userguide/configuration.html#new-lowercase-settings>`__.

CELERY_WORKER_DISABLE_RATE_LIMITS


    Default: ``False``

    Disable the worker rate limits (number of tasks that can be run in a given time frame).

CELERY_WORKER_SEND_TASK_EVENTS


    Default: ``False``

    Send events so the worker can be monitored by other tools.

CLIENT_RESULTS_LIMIT


    | Default: ``5``
    | Env: ``CLIENT_RESULTS_LIMIT``

    The Number of results per page listed in the GeoNode search pages. Different from ``API_LIMIT_PER_PAGE``, affecting the number of items returned by the APIs.

CORS_ALLOW_ALL_ORIGINS


    | Default: ``False``
    | Env: ``CORS_ALLOW_ALL_ORIGINS``

    If set to true `Access-Control-Allow-Origin: *` header is set for any response. A safer option (not managed through env vars at the moment) is `CORS_ALLOWED_ORIGINS`, where a list of hosts can be configured, o `CORS_ALLOWED_ORIGIN_REGEXES`, where the list can contain regexes.
    Notice that the Nginx in front of GeoNode always includes `Access-Control-Allow-Credentials true`. This must also taken into account when CORS is enabled. 

CREATE_LAYER


    | Default: ``False``
    | Env: ``CREATE_LAYER``

    Enable the create layer plugin.

CKAN_ORIGINS


    Default::

        CKAN_ORIGINS = [{
            "label":"Humanitarian Data Exchange (HDX)",
            "url":"https://data.hdx.rwlabs.org/dataset/new?title={name}&notes={abstract}",
            "css_class":"hdx"
        }]

    A list of dictionaries that are used to generate the links to CKAN instances displayed in the Share tab.  For each origin, the name and abstract format parameters are replaced by the actual values of the ResourceBase object (layer, map, document).  This is not enabled by default.  To enable, uncomment the following line: SOCIAL_ORIGINS.extend(CKAN_ORIGINS).

CSRF_COOKIE_HTTPONLY


    | Default: ``False``
    | Env: ``CSRF_COOKIE_HTTPONLY``

    Whether to use HttpOnly flag on the CSRF cookie. If this is set to True, client-side JavaScript will not be able to access the CSRF cookie. This is a `Django Setting <https://docs.djangoproject.com/en/3.2/ref/settings/#csrf-cookie-httponly>`__

CSRF_COOKIE_SECURE


    | Default: ``False``
    | Env: ``CSRF_COOKIE_SECURE``

    Whether to use a secure cookie for the CSRF cookie. If this is set to True, the cookie will be marked as “secure,” which means browsers may ensure that the cookie is only sent with an HTTPS connection. This is a `Django Setting <https://docs.djangoproject.com/en/3.2/ref/settings/#csrf-cookie-secure>`__

CUSTOM_METADATA_SCHEMA


    | Default: ``{}``

    If present, will extend the available metadata schema used for store
    new value for each resource. By default override the existing one.
    The expected schema is the same as the default

## D

DATA_UPLOAD_MAX_NUMBER_FIELDS


    Default: ``100000``

    Maximum value of parsed attributes.


DATASET_DOWNLOAD_HANDLERS


    Default: ``[]``

    Additional download handlers that provides a link to download the resource

DEBUG


    | Default: ``False``
    | Env: ``DEBUG``

    One of the main features of debug mode is the display of detailed error pages. If your app raises an exception when DEBUG is True, Django will display a detailed traceback, including a lot of metadata about your environment, such as all the currently defined Django settings (from settings.py).
    This is a `Django Setting <https://docs.djangoproject.com/en/3.2/ref/settings/#debug>`__

DEFAULT_ANONYMOUS_DOWNLOAD_PERMISSION


    Default: ``True``

    Whether the uploaded resources should downloadable by default.

DEFAULT_ANONYMOUS_VIEW_PERMISSION

    
    Default: ``True``

    Whether the uploaded resources should be public by default.

DEFAULT_AUTO_FIELD


    Default: ``django.db.models.AutoField``

    Default primary key field type to use for models that don’t have a field with primary_key=True.
    Django documentation https://docs.djangoproject.com/it/3.2/ref/settings/#std:setting-DEFAULT_AUTO_FIELD

DEFAULT_DATASET_DOWNLOAD_HANDLER


    Default: ``geonode.layers.download_handler.DatasetDownloadHandler``

    from GeoNode 4.2.x has bee introduced with this issue #11296 and later improved with this issue #11421 
    the concept of Download Handler and ofc GeoNode provides a default implementation of it
    which process the download via WPS

DEFAULT_EXTRA_METADATA_SCHEMA


    Default

    .. code-block:: json

        {
            Optional("id"): int,
            "filter_header": object,
            "field_name": object,
            "field_label": object,
            "field_value": object,
        }

    Define the default metadata schema used for add to the resource extra metadata without modify the actual model.
    This schema is used as validation for the input metadata provided by the user

    - `id`: (optional int): the identifier of the metadata. Optional for creation, required in Upgrade phase
    - `filter_header`: (required object): Can be any type, is used to generate the facet filter header. Is also an identifier.
    - `field_name`: (required object): name of the metadata field
    - `field_label`: (required object): verbose string of the name. Is used as a label in the facet filters.
    - `field_value`: (required object): metadata values

    An example of metadata that can be ingested is the follow:

    .. code-block:: json

        [
            {
                "filter_header": "Bike Brand",
                "field_name": "name",
                "field_label": "Bike Name",
                "field_value": "KTM",
            },
            {
                "filter_header": "Bike Brand",
                "field_name": "name",
                "field_label": "Bike Name",
                "field_value": "Bianchi",
            }
        ]


DEFAULT_LAYER_FORMAT


    | Default: ``image/png``
    | Env: ``DEFAULT_LAYER_FORMAT``

    The default format for requested tile images.


DEFAULT_MAP_CENTER


    | Default: ``(0, 0)``
    | Env: ``DEFAULT_MAP_CENTER_X`` ``DEFAULT_MAP_CENTER_Y``

    A 2-tuple with the latitude/longitude coordinates of the center-point to use
    in newly created maps.

DEFAULT_MAP_CRS


    | Default: ``EPSG:3857``
    | Env: ``DEFAULT_MAP_CRS``

    The default map projection. Default: EPSG:3857

DEFAULT_MAP_ZOOM


    | Default: ``0``
    | Env: ``DEFAULT_MAP_ZOOM``

    The zoom-level to use in newly created maps.  This works like the OpenLayers
    zoom level setting; 0 is at the world extent and each additional level cuts
    the viewport in half in each direction.

DEFAULT_MAX_PARALLEL_UPLOADS_PER_USER


Default: ``5``

When `uploading datasets <../../usage/managing_datasets/uploading_datasets.html#datasets-uploading>`__, 
this value limits the number os parallel uploads.

The parallelism limit is set during installation using the value of this variable.
After installation, only an user with administrative rights can change it.
These limits can be changed in the `admin panel <../../admin/upload-parallelism-limit/index.html#upload-parallelism-limit>`__
or `accessing by api <../../devel/api/V2/index.html#getapi-v2-upload-parallelism-limits->`__.



DEFAULT_MAX_UPLOAD_SIZE


Default: ``104857600`` (100 MB in bytes)

When `uploading datasets <../../usage/managing_datasets/uploading_datasets.html#datasets-uploading>`__
or `uploading documents <../../usage/managing_documents/uploading_documents.html#uploading-documents>`__,
the total size of the uploaded files is verified.

The size limits are set during installation using the value of this variable.
After installation, only an user with administrative rights can change it.
These limits can be changed in the `admin panel <../../admin/upload-size-limits/index.html#upload-size-limits>`__
or `accessing by api <../../devel/api/V2/index.html#getapi-v2-upload-size-limits->`__.


DEFAULT_SEARCH_SIZE


    | Default: ``10``
    | Env: ``DEFAULT_SEARCH_SIZE``

    An integer that specifies the default search size when using ``geonode.search`` for querying data.

DEFAULT_WORKSPACE


    | Default: ``geonode``
    | Env: ``DEFAULT_WORKSPACE``

    The standard GeoServer workspace.

DELAYED_SECURITY_SIGNALS


    | Default: ``False``
    | Env: ``DELAYED_SECURITY_SIGNALS``

    This setting only works when ``GEOFENCE_SECURITY_ENABLED`` has been set to ``True`` and GeoNode is making use of the ``GeoServer BACKEND``.

    By setting this to ``True``, every time the permissions will be updated/changed for a Layer, they won't be applied immediately but only and only if
    either:

    a. A Celery Worker is running and it is able to execute the ``geonode.security.tasks.synch_guardian`` periodic task;
       notice that the task will be executed at regular intervals, based on the interval value defined in the corresponding PeriodicTask model.

    b. A periodic ``cron`` job runs the ``sync_security_rules`` management command, or either it is manually executed from the Django shell.

    c. The user, owner of the Layer or with rights to change its permissions, clicks on the GeoNode UI button ``Sync permissions immediately``

    .. warning:: Layers won't be accessible to public users anymore until the Security Rules are not synchronized!

DISPLAY_COMMENTS


    | Default: ``True``
    | Env: ``DISPLAY_COMMENTS``

    If set to False comments are hidden.


DISPLAY_RATINGS


    | Default: ``True``
    | Env: ``DISPLAY_RATINGS``

    If set to False ratings are hidden.

DISPLAY_SOCIAL


    | Default: ``True``
    | Env: ``DISPLAY_SOCIAL``

    If set to False social sharing is hidden.

DISPLAY_WMS_LINKS


    | Default: ``True``
    | Env: ``DISPLAY_WMS_LINKS``

    If set to False direct WMS link to GeoServer is hidden.

DISPLAY_ORIGINAL_DATASET_LINK


    | Default: ``True``
    | Env: ``DISPLAY_ORIGINAL_DATASET_LINK``

    If set to False original dataset download is hidden.

DOWNLOAD_FORMATS_METADATA


    Specifies which metadata formats are available for users to download.

    Default::

        DOWNLOAD_FORMATS_METADATA = [
            'Atom', 'DIF', 'Dublin Core', 'ebRIM', 'FGDC', 'ISO',
        ]

DOWNLOAD_FORMATS_VECTOR


    Specifies which formats for vector data are available for users to download.

    Default::

        DOWNLOAD_FORMATS_VECTOR = [
            'JPEG', 'PDF', 'PNG', 'Zipped Shapefile', 'GML 2.0', 'GML 3.1.1', 'CSV',
            'Excel', 'GeoJSON', 'KML', 'View in Google Earth', 'Tiles',
        ]

DOWNLOAD_FORMATS_RASTER


    Specifies which formats for raster data are available for users to download.

    Default::

        DOWNLOAD_FORMATS_RASTER = [
            'JPEG', 'PDF', 'PNG' 'Tiles',
        ]

## E

EMAIL_ENABLE


    | Default: ``False``

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

        * EMAIL_USE_SSL

            Default: ``False``

        * DEFAULT_FROM_EMAIL

            Default: ``GeoNode <no-reply@geonode.org>``

EPSG_CODE_MATCHES


    | Default:

    .. code-block:: python

        {
            'EPSG:4326': '(4326) WGS 84',
            'EPSG:900913': '(900913) Google Maps Global Mercator',
            'EPSG:3857': '(3857) WGS 84 / Pseudo-Mercator',
            'EPSG:3785': '(3785 DEPRECATED) Popular Visualization CRS / Mercator',
            'EPSG:32647': '(32647) WGS 84 / UTM zone 47N',
            'EPSG:32736': '(32736) WGS 84 / UTM zone 36S'
        }

    Supported projections human readable descriptions associated to their EPSG Codes.
    This list will be presented to the user during the upload process whenever GeoNode won't be able to recognize a suitable projection.
    Those codes should be aligned to the `UPLOADER` ones and available in GeoServer also.

EXTRA_METADATA_SCHEMA


    | Default:

    .. code-block:: python

        EXTRA_METADATA_SCHEMA = {**{
            "map": os.getenv('MAP_EXTRA_METADATA_SCHEMA', DEFAULT_EXTRA_METADATA_SCHEMA),
            "layer": os.getenv('DATASET_EXTRA_METADATA_SCHEMA', DEFAULT_EXTRA_METADATA_SCHEMA),
            "document": os.getenv('DOCUMENT_EXTRA_METADATA_SCHEMA', DEFAULT_EXTRA_METADATA_SCHEMA),
            "geoapp": os.getenv('GEOAPP_EXTRA_METADATA_SCHEMA', DEFAULT_EXTRA_METADATA_SCHEMA)
        }, **CUSTOM_METADATA_SCHEMA}

    Variable used to actually get the expected metadata schema for each resource_type.
    In this way, each resource type can have a different metadata schema

## F

FREETEXT_KEYWORDS_READONLY


    | Default: ``False``
    | Env: ``FREETEXT_KEYWORDS_READONLY``

    Make Free-Text Keywords writable from users. Or read-only when set to False.


FACET_PROVIDERS


    | Default: ``pre filled list of providers``
    | Env: ``FACET_PROVIDERS``

    Contains the list of the providers available to perform an serve the facets. 
    In case the user wants remove a facets, is enough to remove the path 
    of the proider from the list


## G

GEOFENCE_SECURITY_ENABLED


    | Default: ``True`` (False is Test is true)
    | Env: ``GEOFENCE_SECURITY_ENABLED``

    Whether the geofence security system is used.

GEOIP_PATH


    | Default: ``Path to project``
    | Env: ``PROJECT_ROOT``

    The local path where GeoIPCities.dat is written to. Make sure your user has to have write permissions.

GEONODE_APPS_ENABLED


    | Default: ``True``

    If enabled contrib apps are used.
    If disabled:
    - the geoapps URLs are not included in the routing paths
    - the geoapps resources are excluded from the search
    - the resource detail are forwarded to the homepage

    ``ENABLE -> DISABLE`` transition:
    
    This should be done if the geoapps were enabled in an environment where they are not needed.

    ``DISABLE -> ENABLE`` transition:

    It should be done only once to enable geoapps in an environment where are needed

GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY


    Default:  ``"mapstore"``

    The library to use for display preview images of layers. The library choices are:

     ``"mapstore"``
     ``"leaflet"``
     ``"react"``

GEONODE_EXCHANGE


    | Default:: ``Exchange("default", type="direct", durable=True)``

    The definition of Exchanges published by geonode. Find more about Exchanges at `celery docs <https://docs.celeryproject.org/en/latest/userguide/routing.html#exchanges-queues-and-routing-keys>`__.

GEOSERVER_ADMIN_USER


    | Default: ``admin``
    | Env: ``GEOSERVER_ADMIN_PASSWORD``

    The geoserver admin username.

GEOSERVER_ADMIN_PASSWORD


    | Default: ``geoserver``
    | Env: ``GEOSERVER_ADMIN_USER``

    The GeoServer admin password.

GEOSERVER_FACTORY_PASSWORD


    | Default: ``geoserver``
    | Env: ``GEOSERVER_FACTORY_PASSWORD``

    The GeoServer admin factory password, required for the first time configuration fo Geoserver (Docker setup).

GEOSERVER_EXCHANGE


    | Default:: ``Exchange("geonode", type="topic", durable=False)``

    The definition of Exchanges published by GeoServer. Find more about Exchanges at `celery docs <https://docs.celeryproject.org/en/latest/userguide/routing.html#exchanges-queues-and-routing-keys>`__.

GEOSERVER_LOCATION


    | Default: ``http://localhost:8080/geoserver/``
    | Env: ``GEOSERVER_LOCATION``

    Url under which GeoServer is available.

GEOSERVER_PUBLIC_HOST


    | Default: ``SITE_HOST_NAME`` (Variable)
    | Env: ``GEOSERVER_PUBLIC_HOST``

    Public hostname under which GeoServer is available.

GEOSERVER_PUBLIC_LOCATION


    | Default: ``SITE_HOST_NAME`` (Variable)
    | Env: ``GEOSERVER_PUBLIC_LOCATION``

    Public location under which GeoServer is available.

GEOSERVER_PUBLIC_PORT


    | Default: ``8080 (Variable)``
    | Env: ``GEOSERVER_PUBLIC_PORT``


    Public Port under which GeoServer is available.

GEOSERVER_WEB_UI_LOCATION


    | Default: ``GEOSERVER_PUBLIC_LOCATION (Variable)``
    | Env: ``GEOSERVER_WEB_UI_LOCATION``

    Public location under which GeoServer is available.

GROUP_PRIVATE_RESOURCES


    | Default: ``False``
    | Env: ``GROUP_PRIVATE_RESOURCES``

    If this option is enabled, Resources belonging to a Group won't be visible by others

## I

IMPORTER HANDLERS


    | Default: ``pre filled list of handlers``
    | Env: ``IMPORTER_HANDLERS``

    Contains the list of the handlers available to perform an import of a resource. 
    In case the user wants to drop the support during the import phase, is enough to
    remove the path of the Handler from the list

## L

LEAFLET_CONFIG


    A dictionary used for Leaflet configuration.

LICENSES


    | Default:

    .. code-block:: python

        {
            'ENABLED': True,
            'DETAIL': 'above',
            'METADATA': 'verbose',
        }

    Enable Licenses User Interface

LOCAL_SIGNALS_BROKER_URL


    | Default: ``memory://``

LOCKDOWN_GEONODE


    | Default: ``False``
    | Env: ``LOCKDOWN_GEONODE``

    By default, the GeoNode application allows visitors to view most pages without being authenticated. If this is set to ``True``
    users must be authenticated before accessing URL routes not included in ``AUTH_EXEMPT_URLS``.

LOGIN_URL


    | Default: ``{}account/login/'.format(SITEURL)``
    | Env: ``LOGIN_URL``

    The URL where requests are redirected for login.


LOGOUT_URL


    | Default: ``{}account/login/'.format(SITEURL)``
    | Env: ``LOGOUT_URL``

    The URL where requests are redirected for logout.

## M

MAP_CLIENT_USE_CROSS_ORIGIN_CREDENTIALS


    | Default: ``False``
    | Env: ``MAP_CLIENT_USE_CROSS_ORIGIN_CREDENTIALS``

    Enables cross origin requests for geonode-client.

MAPSTORE_BASELAYERS


    | Default:

    .. code-block:: python

        [
            {
                "type": "osm",
                "title": "Open Street Map",
                "name": "mapnik",
                "source": "osm",
                "group": "background",
                "visibility": True
            }, {
                "type": "tileprovider",
                "title": "OpenTopoMap",
                "provider": "OpenTopoMap",
                "name": "OpenTopoMap",
                "source": "OpenTopoMap",
                "group": "background",
                "visibility": False
            }, {
                "type": "wms",
                "title": "Sentinel-2 cloudless - https://s2maps.eu",
                "format": "image/jpeg",
                "id": "s2cloudless",
                "name": "s2cloudless:s2cloudless",
                "url": "https://maps.geo-solutions.it/geoserver/wms",
                "group": "background",
                "thumbURL": "%sstatic/mapstorestyle/img/s2cloudless-s2cloudless.png" % SITEURL,
                "visibility": False
           }, {
                "source": "ol",
                "group": "background",
                "id": "none",
                "name": "empty",
                "title": "Empty Background",
                "type": "empty",
                "visibility": False,
                "args": ["Empty Background", {"visibility": False}]
           }
        ]

    | Env: ``MAPSTORE_BASELAYERS``

    Allows to specify which backgrounds MapStore should use. The parameter ``visibility`` for a layer, specifies which one is the default one.

    A sample configuration using the Bing background without OpenStreetMap, could be the following one:

    .. code-block:: python

        [
            {
                "type": "bing",
                "title": "Bing Aerial",
                "name": "AerialWithLabels",
                "source": "bing",
                "group": "background",
                "apiKey": "{{apiKey}}",
                "visibility": True
            }, {
                "type": "tileprovider",
                "title": "OpenTopoMap",
                "provider": "OpenTopoMap",
                "name": "OpenTopoMap",
                "source": "OpenTopoMap",
                "group": "background",
                "visibility": False
            }, {
                "type": "wms",
                "title": "Sentinel-2 cloudless - https://s2maps.eu",
                "format": "image/jpeg",
                "id": "s2cloudless",
                "name": "s2cloudless:s2cloudless",
                "url": "https://maps.geo-solutions.it/geoserver/wms",
                "group": "background",
                "thumbURL": "%sstatic/mapstorestyle/img/s2cloudless-s2cloudless.png" % SITEURL,
                "visibility": False
           }, {
                "source": "ol",
                "group": "background",
                "id": "none",
                "name": "empty",
                "title": "Empty Background",
                "type": "empty",
                "visibility": False,
                "args": ["Empty Background", {"visibility": False}]
           }
        ]

    .. warning:: To use a Bing background, you need to correctly set and provide a valid ``BING_API_KEY``

MAX_DOCUMENT_SIZE


    | Default:``2``
    | Env: ``MAX_DOCUMENT_SIZE``

    Allowed size for documents in MB.

METADATA_PARSERS


Is possible to define multiple XML parsers for ingest XML during the layer upload.

The variable should be declared in this way in `settings.py`:

`METADATA_PARSERS = ['list', 'of', 'parsing', 'functions']`

If you want to always use the default metadata parser and after use your own, the variable must be set with first value as `__DEFAULT__`
Example:

`METADATA_PARSERS = ['__DEFAULT__', 'custom_parsing_function]`

If not set, the system will use the `__DEFAULT__` parser.

The custom parsing function must be accept in input 6 parameter that are:
    
    | - exml (xmlfile)
    | - uuid (str)
    | - vals (dict)
    | - regions (list)
    | - keywords (list)
    | - custom (dict)

If you want to use your parser after the default one, here is how the variable are populated:
    
    | - exml: the XML file to parse
    | - uuid: the UUID of the layer
    | - vals: Dictionary of information that belong to ResourceBase
    | - regions: List of regions extracted from the XML
    | - keywords: List of dict of keywords already divided between free-text and thesarus
    | - custom: Custom varible

NOTE: the keywords must be in a specific format, since later this dict, will be ingested by the `KeywordHandler` which will assign the keywords/thesaurus to the layer.

    .. code::
        {
            "keywords": [list_of_keyword_extracted],
            "thesaurus": {"date": None, "datetype": None, "title": None}, # thesaurus informations
            "type": theme,  #extracted theme if present
        }
        
Here is an example of expected parser function

    .. code::
        def custom_parsing_function(exml, uuid, vals, regions, keywords, custom):
            # Place here your code
            return uuid, vals, regions, keywords, custom

For more information, please rely to `TestCustomMetadataParser` which contain a smoke test to explain the functionality

            
METADATA_STORERS


Is possible to define multiple Layer storer during the layer upload.

The variable should be declared in this way:

`METADATA_STORERS = ['custom_storer_function']`

NOTE: By default the Layer is always saved with the default behaviour.

The custom storer function must be accept in input 2 parameter that are:
    
    | - Layer (layer model instance)
    | - custom (dict)

Here is how the variable are populated by default:
    
    | - layer (layer model instance) that we wanto to change
    | - custom: custom dict populated by the parser

Here is an example of expected storer function

    .. code::
        def custom_storer_function(layer, custom):
            # do something here
            pass

For more information, please rely to `TestMetadataStorers` which contain a smoke test to explain the functionality


MISSING_THUMBNAIL


    Default: ``geonode/img/missing_thumb.png``

    The path to an image used as thumbnail placeholder.


MEMCACHED_BACKEND

    Default: ``django.core.cache.backends.memcached.PyMemcacheCache``

    Define which backend of memcached will be used


MEMCACHED_ENABLED

    Default: ``False``

    If True, will use MEMCACHED_BACKEND as default backend in CACHES


MODIFY_TOPICCATEGORY


    Default: ``False``

    Metadata Topic Categories list should not be modified, as it is strictly defined
    by ISO (See: http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml
    and check the <CodeListDictionary gml:id="MD_MD_TopicCategoryCode"> element).

    Some customization is still possible changing the is_choice and the GeoNode
    description fields.

    In case it is necessary to add/delete/update categories, it is
    possible to set the MODIFY_TOPICCATEGORY setting to True.

MONITORING_ENABLED


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


    | Default: ``365``
    | Env: ``MONITORING_DATA_TTL``

    How long monitoring data should be stored in days.

MONITORING_DISABLE_CSRF


    | Default: ``False``
    | Env: ``MONITORING_DISABLE_CSRF``

    Set this to true to disable csrf check for notification config views, use with caution - for dev purpose only.

.. _monitoring-skip-paths:

MONITORING_SKIP_PATHS


    Default:

    .. code::

        (
            '/api/o/',
            '/monitoring/',
            '/admin',
            '/jsi18n',
            STATIC_URL,
            MEDIA_URL,
            re.compile('^/[a-z]{2}/admin/'),
        )

    Skip certain useless paths to not to mud analytics stats too much.
    See :ref:`geonode_monitoring` to learn more about it.

    This setting takes effects only if :ref:`user-analytics` is true.

## N

NOTIFICATIONS_MODULE


    Default: ``pinax.notifications``

    App used for notifications. (pinax.notifications or notification)

NOTIFICATION_ENABLED


    | Default: ``True``
    | Env: ``NOTIFICATION_ENABLED``

    Enable or disable the notification system.

## O

OAUTH2_API_KEY


    | Default: ``None``
    | Env: ``OAUTH2_API_KEY``

    In order to protect oauth2 REST endpoints, used by GeoServer to fetch user roles and infos, you should set this key and configure the ``geonode REST role service`` accordingly. Keep it secret!

    .. warning:: If not set, the endpoint can be accessed by users without authorization.

OAUTH2_PROVIDER


    Ref.: `OAuth Toolkit settings <https://django-oauth-toolkit.readthedocs.io/en/latest/settings.html>`__

OAUTH2_PROVIDER_APPLICATION_MODEL


    | Default: ``oauth2_provider.Application``

    Ref.: `OAuth Toolkit settings <https://django-oauth-toolkit.readthedocs.io/en/latest/settings.html>`__

OAUTH2_PROVIDER_ACCESS_TOKEN_MODEL


    | Default: ``oauth2_provider.AccessToken``

    Ref.: `OAuth Toolkit settings <https://django-oauth-toolkit.readthedocs.io/en/latest/settings.html>`__

OAUTH2_PROVIDER_ID_TOKEN_MODEL


    | Default: ``oauth2_provider.IDToken``

    Ref.: `OAuth Toolkit settings <https://django-oauth-toolkit.readthedocs.io/en/latest/settings.html>`__

OAUTH2_PROVIDER_GRANT_MODEL


    | Default: ``oauth2_provider.Grant``

    Ref.: `OAuth Toolkit settings <https://django-oauth-toolkit.readthedocs.io/en/latest/settings.html>`__

OAUTH2_PROVIDER_REFRESH_TOKEN_MODEL


    | Default: ``oauth2_provider.RefreshToken``

    Ref.: `OAuth Toolkit settings <https://django-oauth-toolkit.readthedocs.io/en/latest/settings.html>`__

OGC_SERVER


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


    | Default: ``http://geodata.tufts.edu/solr/select``
    | Env: ``OGP_URL``

    Endpoint of geodata.tufts.edu getCapabilities.

OPENGRAPH_ENABLED


    Default:: ``True``

    A boolean that specifies whether Open Graph is enabled.  Open Graph is used by Facebook and Slack.

## P

PINAX_NOTIFICATIONS_BACKENDS


    Default: ``("email", _EMAIL_BACKEND, 0),``

    Used notification backend. This is a `pinax notification setting: <https://django-notification.readthedocs.io/en/latest/settings.html#pinax-notifications-backends>`__

PINAX_NOTIFICATIONS_LOCK_WAIT_TIMEOUT


    | Default: ``-1``
    | Env: ``NOTIFICATIONS_LOCK_WAIT_TIMEOUT``

    It defines how long to wait for the lock to become available. Default of -1 means to never wait for the lock to become available.
    This is a `pinax notification setting: <https://django-notification.readthedocs.io/en/latest/settings.html#pinax-notifications-lock-wait-timeout>`__

PINAX_NOTIFICATIONS_QUEUE_ALL


    | Default: ``-1``
    | Env: ``NOTIFICATIONS_LOCK_WAIT_TIMEOUT``

    By default, calling notification.send will send the notification immediately, however, if you set this setting to True, then the default behavior of the send method will be to queue messages in the database for sending via the emit_notices command.
    This is a `pinax notification setting: <https://django-notification.readthedocs.io/en/latest/settings.html#pinax-notifications-queue-all>`__

PINAX_RATINGS_CATEGORY_CHOICES


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


PROFILE_EDIT_EXCLUDE_FIELD

    | Default: ``[]``

    A list of element (item name) to exclude from the Profile Edit page.

    Example:
    
    ``PROFILE_EDIT_EXCLUDE_FIELD=['organization', 'language']``


PROXY_ALLOWED_HOSTS


    Default: ``()`` (Empty tuple)

    A tuple of strings representing the host/domain names that GeoNode can proxy requests to. This is a security measure
    to prevent an attacker from using the GeoNode proxy to render malicious code or access internal sites.

    Values in this tuple can be fully qualified names (e.g. 'www.geonode.org'), in which case they will be matched against
    the request’s Host header exactly (case-insensitive, not including port). A value beginning with a period can be used
    as a subdomain wildcard: ``.geonode.org`` will match geonode.org, www.geonode.org, and any other subdomain of
    geonode.org. A value of '*' will match anything and is not recommended for production deployments.


PROXY_URL


    Default ``/proxy/?url=``

    The URL to a proxy that will be used when making client-side requests in GeoNode.  By default, the
    internal GeoNode proxy is used but administrators may favor using their own, less restrictive proxies.


PYCSW


    A dict with pycsw's configuration with two possible keys CONFIGURATION and FILTER.
    
    CONFIGURATION
    Of note are the sections ``metadata:main`` to set CSW server metadata and ``metadata:inspire``
    to set INSPIRE options.  Setting ``metadata:inspire['enabled']`` to ``true``
    will enable INSPIRE support.   Server level configurations can be overridden
    in the ``server`` section.  See http://docs.pycsw.org/en/latest/configuration.html
    for full pycsw configuration details.

    FILTER
    Optional settings in order to add a filter to the CSW filtering.
    The filter follow the django orm structure and must be a `ResourceBase` field/related field.
    By default CSW will filter only for `layer` resource_type

    Example of PYCSW configuration.
    PYCSW: {
        'CONFIGURATION': {...},
        'FILTER': {'resource_type__in':['layer'] }
    }
    
## R

RABBITMQ_SIGNALS_BROKER_URL


    Default: ``amqp://localhost:5672``

    The Rabbitmq endpoint

.. _recaptcha_enabled:

RECAPTCHA_ENABLED


    | Default: ``False``
    | Env: ``RECAPTCHA_ENABLED``

    Allows enabling reCaptcha field on signup form.
    Valid Captcha Public and Private keys will be needed as specified here https://pypi.org/project/django-recaptcha/#installation

    You will need to generate a keys pair for ``reCaptcha v2`` for your domain from https://www.google.com/recaptcha/admin/create

    More options will be available by enabling this setting:

    * **ACCOUNT_SIGNUP_FORM_CLASS**

        | Default: ``geonode.people.forms.AllauthReCaptchaSignupForm``
        | Env: ``ACCOUNT_SIGNUP_FORM_CLASS``

        Enabled only when the :ref:`recaptcha_enabled` option is ``True``.

    * **INSTALLED_APPS**

        The ``captcha`` must be present on ``INSTALLED_APPS``, otherwise you'll get an error.

        When enabling the :ref:`recaptcha_enabled` option through the ``environment``, this setting will be automatically added by GeoNode as follows:

        .. code:: python

            if 'captcha' not in INSTALLED_APPS:
                    INSTALLED_APPS += ('captcha',)

    * **RECAPTCHA_PUBLIC_KEY**

        | Default: ``geonode_RECAPTCHA_PUBLIC_KEY``
        | Env: ``RECAPTCHA_PUBLIC_KEY``

        You will need to generate a keys pair for ``reCaptcha v2`` for your domain from https://www.google.com/recaptcha/admin/create

        For mode details on the reCaptcha package, please see:

        #. https://pypi.org/project/django-recaptcha/#installation
        #. https://pypi.org/project/django-recaptcha/#local-development-and-functional-testing

    * **RECAPTCHA_PRIVATE_KEY**

        | Default: ``geonode_RECAPTCHA_PRIVATE_KEY``
        | Env: ``RECAPTCHA_PRIVATE_KEY``

        You will need to generate a keys pair for ``reCaptcha v2`` for your domain from https://www.google.com/recaptcha/admin/create

        For mode details on the reCaptcha package, please see:

        #. https://pypi.org/project/django-recaptcha/#installation
        #. https://pypi.org/project/django-recaptcha/#local-development-and-functional-testing

RECAPTCHA_PUBLIC_KEY


    | Default: ``geonode_RECAPTCHA_PUBLIC_KEY``
    | Env: ``RECAPTCHA_PUBLIC_KEY``

    You will need to generate a keys pair for ``reCaptcha v2`` for your domain from https://www.google.com/recaptcha/admin/create

    Ref. to :ref:`recaptcha_enabled`

RECAPTCHA_PRIVATE_KEY


    | Default: ``geonode_RECAPTCHA_PRIVATE_KEY``
    | Env: ``RECAPTCHA_PRIVATE_KEY``

    You will need to generate a keys pair for ``reCaptcha v2`` for your domain from https://www.google.com/recaptcha/admin/create

    Ref. to :ref:`recaptcha_enabled`

REDIS_SIGNALS_BROKER_URL


    Default: ``redis://localhost:6379/0``

    The Redis endpoint.

REGISTERED_MEMBERS_GROUP_NAME


    | Default: ``registered-members``
    | Env: ``REGISTERED_MEMBERS_GROUP_NAME``

    Used by ``AUTO_ASSIGN_REGISTERED_MEMBERS_TO_REGISTERED_MEMBERS_GROUP_NAME`` settings.

REGISTERED_MEMBERS_GROUP_TITLE


    | Default: ``Registered Members``
    | Env: ``REGISTERED_MEMBERS_GROUP_TITLE``

    Used by ``AUTO_ASSIGN_REGISTERED_MEMBERS_TO_REGISTERED_MEMBERS_GROUP_NAME`` settings.

REGISTRATION_OPEN


    Default: ``False``

    A boolean that specifies whether users can self-register for an account on your site.

RESOURCE_PUBLISHING


    Default: ``False``

    By default, the GeoNode application allows GeoNode staff members to
    publish/unpublish resources.
    By default, resources are published when created. When this setting is set to
    True the staff members will be able to unpublish a resource (and eventually
    publish it back).

## S

SEARCH_FILTERS


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


    | Default: ``True``
    | Env: ``SECURE_BROWSER_XSS_FILTER``

    If True, the SecurityMiddleware sets the X-XSS-Protection: 1; mode=block header on all responses that do not already have it.
    This is `<Django settings. https://docs.djangoproject.com/en/3.2/ref/settings/#secure-browser-xss-filter>`__

SECURE_CONTENT_TYPE_NOSNIFF


    | Default: ``True``
    | Env: ``SECURE_CONTENT_TYPE_NOSNIFF``

    If True, the SecurityMiddleware sets the X-Content-Type-Options: nosniff header on all responses that do not already have it.
    This is `Django settings: <https://docs.djangoproject.com/en/3.2/ref/settings/#secure-content-type-nosniff>`__


SECURE_HSTS_INCLUDE_SUBDOMAINS


    | Default: ``True``
    | Env: ``SECURE_HSTS_INCLUDE_SUBDOMAINS``

    This is Django settings: https://docs.djangoproject.com/en/3.2/ref/settings/#secure-hsts-include-subdomains

SECURE_HSTS_SECONDS


    | Default: ``3600``
    | Env: ``SECURE_HSTS_SECONDS``

    This is `Django settings: <https://docs.djangoproject.com/en/3.2/ref/settings/#secure-hsts-seconds>`__
    If set to a non-zero integer value, the SecurityMiddleware sets the HTTP Strict Transport Security header on all responses that do not already have it.

SECURE_SSL_REDIRECT


    If True, the SecurityMiddleware redirects all non-HTTPS requests to HTTPS (except for those URLs matching a regular expression listed in SECURE_REDIRECT_EXEMPT).
    This is `Django settings: <https://docs.djangoproject.com/en/3.2/ref/settings/#secure-ssl-redirect>`__

SERVICES_TYPE_MODULES


It's possible to define multiple Service Types Modules for custom service type with it's own Handler.

The variable should be declared in this way in `settings.py`:

`SERVICES_TYPE_MODULES = [ 'path.to.module1','path.to.module2', ... ]`

Default service types are already included

Inside each module in the list we need to define a variable:

`services_type = {
    "<key_of_service_type>": {
        "OWS": True/False,
        "handler": "<path.to.Handler>",
        "label": "<label to show in remote service page>",
        "management_view": "<path.to.view>"
    }
}`

the key_of_service_type is just an identifier to assign at the service type.
OWS is True if the service type is an OGC Service Compliant.
The handler key must contain the path to the class who will provide all methods to manage the service type
The label is what is shown in the service form when adding a new service.
The management_view, if exists, must contain the path to the method where the management page is opened.

SERVICE_UPDATE_INTERVAL


    | Default: ``0``

    The Interval services are updated.

SESSION_COOKIE_SECURE


    | Default: ``False``
    | Env: ``SESSION_COOKIE_SECURE``

    This is a `Django setting: <https://docs.djangoproject.com/en/3.2/ref/settings/#session-cookie-secure>`__

SESSION_EXPIRED_CONTROL_ENABLED


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


    Default: ``False``

    A boolean which specifies whether to display the email in the user’s profile.

SITE_HOST_NAME


    | Default: ``localhost``
    | Env: ``SITE_HOST_NAME``

    The hostname used for GeoNode.

SITE_HOST_PORT


    | Default: ``8000``
    | Env: ``SITE_HOST_PORT``

    The Site hostport.

SITEURL


    Default: ``'http://localhost:8000/'``

    A base URL for use in creating absolute links to Django views and generating links in metadata.

SIZE_RESTRICTED_FILE_UPLOAD_ELEGIBLE_URL_NAMES 


    Default: ``'("data_upload", "uploads-upload", "document_upload",)'``

    Rappresent the list of the urls basename that are under file_size restriction

SKIP_PERMS_FILTER


    | Default: ``False``
    | Env: ``SKIP_PERMS_FILTER``

    If set to true permissions prefiltering is avoided.

SOCIALACCOUNT_ADAPTER


    Default: ``geonode.people.adapters.SocialAccountAdapter``

    This is a `django-allauth setting <https://django-allauth.readthedocs.io/en/latest/configuration.html#configuration>`__
    It allows specifying a custom class to handle authentication for social accounts.

SOCIALACCOUNT_AUTO_SIGNUP


    Default: ``True``

    Attempt to bypass the signup form by using fields (e.g. username, email) retrieved from the social account provider.
    This is a `Django-allauth setting: <https://django-allauth.readthedocs.io/en/latest/configuration.html>`__


SOCIALACCOUNT_PROVIDERS


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


  Default::

      {
          "facebook": "geonode.people.profileextractors.FacebookExtractor",
          "linkedin_oauth2": "geonode.people.profileextractors.LinkedInExtractor",
      }

  A dictionary with provider ids as keys and path to custom profile extractor
  classes as values.

SOCIAL_BUTTONS


    Default: ``True``

    A boolean which specifies whether the social media icons and JavaScript should be rendered in GeoNode.

SOCIAL_ORIGINS


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

SOCIALACCOUNT_WITH_GEONODE_LOCAL_SINGUP


    Default: ``True``

    Variable which controls displaying local account registration form. By default form is visible

SRID


    Default::

        {
        'DETAIL': 'never',
        }

SEARCH_RESOURCES_EXTENDED


    Default: ``True``

    This will extend search with additinoal properties. By default its on and search engine will check resource title or purpose or abstract.
    When set to False just title lookup is performed.

SUPPORTED_DATASET_FILE_TYPES

    
    Default::
        SUPPORTED_DATASET_FILE_TYPES = [
        {
            "id": "shp",
            "label": "ESRI Shapefile",
            "format": "vector",
            "ext": ["shp"],
            "requires": ["shp", "prj", "dbf", "shx"],
            "optional": ["xml", "sld"]
        },
        {
            "id": "tiff",
            "label": "GeoTIFF",
            "format": "raster",
            "ext": ["tiff", "tif"],
            "mimeType": ["image/tiff"],
            "optional": ["xml", "sld"]
        },
        {
            "id": "csv",
            "label": "Comma Separated Value (CSV)",
            "format": "vector",
            "ext": ["csv"],
            "mimeType": ["text/csv"],
            "optional": ["xml", "sld"]
        },
        {
            "id": "zip",
            "label": "Zip Archive",
            "format": "archive",
            "ext": ["zip"],
            "mimeType": ["application/zip"],
            "optional": ["xml", "sld"]
        },
        {
            "id": "xml",
            "label": "XML Metadata File",
            "format": "metadata",
            "ext": ["xml"],
            "mimeType": ["application/json"],
            "needsFiles": ["shp", "prj", "dbf", "shx", "csv", "tiff", "zip", "sld"]
        },
        {
            "id": "sld",
            "label": "Styled Layer Descriptor (SLD)",
            "format": "metadata",
            "ext": ["sld"],
            "mimeType": ["application/json"],
            "needsFiles": ["shp", "prj", "dbf", "shx", "csv", "tiff", "zip", "xml"]
        }
    ]

    Rappresent the list of the supported file type in geonode that can be ingested by the platform

For example. the following configuration is needed to add the GeoJSON as supported file:

    Default::
        {
            "id": "geojson",
            "label": "GeoJSON",
            "format": "metadata",
            "ext": ["geojson"],
            "mimeType": ["application/json"]
        }


## T

TASTYPIE_DEFAULT_FORMATS


    Default: ``json``

    This setting allows you to globally configure the list of allowed serialization formats for your entire site.
    This is a `tastypie setting: <https://django-tastypie.readthedocs.io/en/v0.9.14/settings.html#tastypie-default-formats>`__

THEME_ACCOUNT_CONTACT_EMAIL


    Default: ``'admin@example.com'``

    This email address is added to the bottom of the password reset page in case users have trouble unlocking their account.

THESAURI


    Default = ``[]``

    A list of Keywords thesauri settings:
    For example `THESAURI = [{'name':'inspire_themes', 'required':True, 'filter':True}, {'name':'inspire_concepts', 'filter':True}, ]`

TOPICCATEGORY_MANDATORY


    | Default: ``False``
    | Env: ``TOPICCATEGORY_MANDATORY``

    If this option is enabled, Topic Categories will become strictly Mandatory on Metadata Wizard

TWITTER_CARD


    Default:: ``True``

    A boolean that specifies whether Twitter cards are enabled.

TWITTER_SITE


    Default:: ``'@GeoNode'``

    A string that specifies the site to for the twitter:site meta tag for Twitter Cards.

TWITTER_HASHTAGS


    Default:: ``['geonode']``

    A list that specifies the hashtags to use when sharing a resource when clicking on a social link.

.. _tinyMCE Default Config Settings:

TINYMCE_DEFAULT_CONFIG


    Default::

        {
            "selector": "textarea#id_resource-featureinfo_custom_template",
            "theme": "silver",
            "height": 500,
            "plugins": 'print preview paste importcss searchreplace autolink autosave save directionality code visualblocks visualchars fullscreen image link media template codesample table charmap hr pagebreak nonbreaking anchor toc insertdatetime advlist lists wordcount imagetools textpattern noneditable help charmap quickbars emoticons',
            "imagetools_cors_hosts": ['picsum.photos'],
            "menubar": 'file edit view insert format tools table help',
            "toolbar": 'undo redo | bold italic underline strikethrough | fontselect fontsizeselect formatselect | alignleft aligncenter alignright alignjustify | outdent indent |  numlist bullist | forecolor backcolor removeformat | pagebreak | charmap emoticons | fullscreen  preview save | insertfile image media template link anchor codesample | ltr rtl',
            "toolbar_sticky": "true",
            "autosave_ask_before_unload": "true",
            "autosave_interval": "30s",
            "autosave_prefix": "{path}{query}-{id}-",
            "autosave_restore_when_empty": "false",
            "autosave_retention": "2m",
            "image_advtab": "true",
            "content_css": '//www.tiny.cloud/css/codepen.min.css',
            "importcss_append": "true",
            "image_caption": "true",
            "quickbars_selection_toolbar": 'bold italic | quicklink h2 h3 blockquote quickimage quicktable',
            "noneditable_noneditable_class": "mceNonEditable",
            "toolbar_mode": 'sliding',
            "contextmenu": "link image imagetools table",
            "templates": [
                {
                    "title": 'New Table',
                    "description": 'creates a new table',
                    "content": '<div class="mceTmpl"><table width="98%%"  border="0" cellspacing="0" cellpadding="0"><tr><th scope="col"> </th><th scope="col"> </th></tr><tr><td> </td><td> </td></tr></table></div>'
                },
                {
                    "title": 'Starting my story',
                    "description": 'A cure for writers block',
                    "content": 'Once upon a time...'
                },
                {
                    "title": 'New list with dates',
                    "description": 'New List with dates',
                    "content": '<div class="mceTmpl"><span class="cdate">cdate</span><br /><span class="mdate">mdate</span><h2>My List</h2><ul><li></li><li></li></ul></div>'
                }
            ],
            "template_cdate_format": '[Date Created (CDATE): %m/%d/%Y : %H:%M:%S]',
            "template_mdate_format": '[Date Modified (MDATE): %m/%d/%Y : %H:%M:%S]',
        }

    HTML WYSIWYG Editor (TINYMCE) Menu Bar Settings. For more info see:

        -   https://django-tinymce.readthedocs.io/en/latest/installation.html#configuration
        -   :ref:`getfetureinfo-templates`
## U

UI_REQUIRED_FIELDS

If this option is enabled, the input selected (we are referring to the one present in the optional Metadata-Tab on the Metadata-Wizard) will become mandatory.

The fields that can be mandatory are:

    | id_resource-edition => Label: Edition
    | id_resource-purpose => Label: Purpose
    | id_resource-supplemental_information =>  Label: Supplemental information 
    | id_resource-temporal_extent_start_pickers => Label: temporal extent start
    | id_resource-temporal_extent_end => Label:  temporal extent end
    | id_resource-maintenance_frequency => Label:  Maintenance frequency
    | id_resource-spatial_representation_type => Label:  Spatial representation type 

If at least one on the above ids is set in this configuration, the panel header will change from `Optional` to `Mandatory`

    | Confiugration Example:
    | UI_REQUIRED_FIELDS = ['id_resource-edition']


UNOCONV_ENABLE


    | Default: ``False``
    | Env: ``UNOCONV_ENABLE``

UPLOADER


    Default::

        {
            'BACKEND' : 'geonode.importer',
            'OPTIONS' : {
                'TIME_ENABLED': False,
            }
        }

    A dictionary of Uploader settings and their values.

    * BACKEND

        Default: ``'geonode.importer'``

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


    | Default: ``True``
    | Env: ``USER_MESSAGES_ALLOW_MULTIPLE_RECIPIENTS``

    Set to true to have multiple recipients in /message/create/

.. _user-deletion-rules:

USER_DELETION_RULES

    | Default: ``["geonode.people.utils.user_has_resources"]``
    | Env: ``USER_DELETION_RULES``

    List of callables that will be called the deletion of a user account is requested.
    The deletion will fail if any of the callables return ``False``. 
    New rules can be added, as a string path to the callable, as long as they take as parameter
    the user object and return a boolean.

.. _user-analytics:


UUID HANDLER


Is possible to define an own uuidhandler for the Layer.

To start using your own handler, is needed to add the following configuration:

`LAYER_UUID_HANDLER = "mymodule.myfile.MyObject"`

The Object must accept as `init` the `instance` of the layer and have a method named `create_uuid()`

here is an example:

    | class MyObject():
    |    def __init__(self, instance):
    |        self.instance = instance
    |
    |    def create_uuid(self):
    |        # here your code
    |        pass


## X

X_FRAME_OPTIONS


Default: ``'ALLOW-FROM %s' % SITEURL``

This is a `Django setting <https://docs.djangoproject.com/en/3.2/ref/clickjacking/#setting-x-frame-options-for-all-responses>`__
