# Settings

Here’s a list of settings available in GeoNode and their default values.  This includes settings for some external applications that
GeoNode depends on.

For most of them, default values are good. Those should be changed only for advanced configurations in production or heavily hardened systems.

The most common ones can be set through ``environment`` variables to avoid touching the ``settings.py`` file at all.
This is a good practice and also the preferred one to configure GeoNode (and Django apps in general).
Whenever you need to change them, set the environment variable accordingly (where it is available) instead of overriding it through the ``local_settings``.


## A

**ACCESS_TOKEN_EXPIRE_SECONDS**

:   - :   Default:  ``86400``
    - Env: ``ACCESS_TOKEN_EXPIRE_SECONDS``

When a user logs into GeoNode, if no ``ACCESS_TOKEN`` exists, a new one will be created with a default expiration time of ``ACCESS_TOKEN_EXPIRE_SECONDS`` seconds (1 day by default).

**ACCOUNT_ADAPTER**

:   - :   Default:  ``geonode.people.adapters.LocalAccountAdapter``

Custom GeoNode People (Users) Account Adapter.

**ACCOUNT_APPROVAL_REQUIRED**

:   - Default ``False``
    - Env: ``ACCOUNT_APPROVAL_REQUIRED``

If ``ACCOUNT_APPROVAL_REQUIRED`` equals ``True``, newly registered users must be activated by a superuser through the Admin gui, before they can access GeoNode.

**ACCOUNT_CONFIRM_EMAIL_ON_GET**

:   - Default ``True``

This is a [django-allauth setting](https://django-allauth.readthedocs.io/en/latest/configuration.html#configuration)
It allows specifying the HTTP method used when confirming e-mail addresses.

**ACCOUNT_EMAIL_REQUIRED**

:   - Default ``True``

This is a deprecated.
Use ``ACCOUNT_SIGNUP_FIELDS`` instead.
It controls whether the user is required to provide an e-mail address upon registration.

**ACCOUNT_EMAIL_VERIFICATION**

:   - Default ``optional``

This is a [django-allauth setting](https://django-allauth.readthedocs.io/en/latest/configuration.html#configuration)

**ACCOUNT_LOGIN_METHODS**

:   - Default ``{'email', 'username'}``
    - Env: ``ACCOUNT_LOGIN_METHODS``

This is a [django-allauth setting](https://docs.allauth.org/en/dev/account/configuration.html)
which controls which identifiers users can use to log in.

**ACCOUNT_LOGIN_REDIRECT_URL**


:   - Default ``SITEURL``
    - Env: ``LOGIN_REDIRECT_URL``

This is a [django-user-accounts setting](https://django-user-accounts.readthedocs.io/en/latest/settings.html)
It allows specifying the default redirect URL after a successful login.

**ACCOUNT_LOGOUT_REDIRECT_URL**


:   - Default ``SITEURL``
    - Env: ``LOGOUT_REDIRECT_URL``

This is a [django-user-accounts setting](https://django-user-accounts.readthedocs.io/en/latest/settings.html)
It allows specifying the default redirect URL after a successful logout.

**ACCOUNT_NOTIFY_ON_PASSWORD_CHANGE**


:   - Default ``True``
    - Env: ``ACCOUNT_NOTIFY_ON_PASSWORD_CHANGE``

This is a [django-user-accounts setting](https://django-user-accounts.readthedocs.io/en/latest/settings.html)

**ACCOUNT_OPEN_SIGNUP**


:   - Default ``True``
    - Env: ``ACCOUNT_OPEN_SIGNUP``

This is a [django-user-accounts setting](https://django-user-accounts.readthedocs.io/en/latest/settings.html)
Whether or not people are allowed to self-register to GeoNode or not.

**ACCOUNT_SIGNUP_FIELDS**

:   - Default ``['email*', 'username*', 'password1*', 'password2*']``
    - Env: ``ACCOUNT_SIGNUP_FIELDS``

This is a [django-allauth setting](https://docs.allauth.org/en/dev/account/configuration.html)
which controls which fields are shown during signup. Fields marked with ``*`` are required.

**ACCOUNT_SIGNUP_FORM_CLASS**


:   - Default ``geonode.people.forms.AllauthReCaptchaSignupForm``
    - Env: ``ACCOUNT_SIGNUP_FORM_CLASS``

Enabled only when the :ref:`recaptcha_enabled` option is ``True``.

Ref. to :ref:`recaptcha_enabled`

**ACTSTREAM_SETTINGS**


:   - Default

{
'FETCH_RELATIONS': True,
'USE_PREFETCH': False,
'USE_JSONFIELD': True,
'GFK_FETCH_DEPTH': 1,
}

Actstream Settings.


**ADDITIONAL_DATASET_FILE_TYPES**


External application can define additional supported file type other than the default one declared in the `SUPPORTED_DATASET_FILE_TYPES` .

The variable should be declared in this way in `settings.py` (or via application hook):


```python
ADDITIONAL_DATASET_FILE_TYPES=[
    {
    "id": "dummy_type",
    "label": "Dummy Type",
    "format": "dummy",
    "ext": ["dummy"]
    },
]
```

Please rely on geonode.tests.test_utils.TestSupportedTypes for an example

**ADMIN_IP_WHITELIST**


:   - Default ``[]``

When this list is popuplated with a list of IPs or IP ranges (e.g. 192.168.1.0/24) requests from and admin user will be allowe only from IPs matching with the list.

**ADMIN_MODERATE_UPLOADS**


:   - Default ``False``

When this variable is set to ``True``, every uploaded resource must be approved before becoming visible to the public users.

Until a resource is in ``PENDING APPROVAL`` state, only the superusers, owner and group members can access it, unless specific edit permissions have been set for other users or groups.

A ``Group Manager`` *can* approve the resource, but he cannot publish it whenever the setting ``RESOURCE_PUBLISHING`` is set to ``True``.
Otherwise, if ``RESOURCE_PUBLISHING`` is set to ``False``, the resource becomes accessible as soon as it is approved.

**ADMINS_ONLY_NOTICE_TYPES**


:   - Default ``['monitoring_alert',]``

A list of notification labels that standard users should not either see or set.

Such notifications will be hidden from the notify settings page and automatically set to false for non-superusers.


**ADVANCED_EDIT_EXCLUDE_FIELD**

:   - Default ``[]``

A list of element (item name) to exclude from the Advanced Edit page.

Example:

``ADVANCED_EDIT_EXCLUDE_FIELD=['title', 'keywords', 'tkeywords']``


**AGON_RATINGS_CATEGORY_CHOICES**


:   - Default:
    ```python
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
    ```

**ALLOWED_DOCUMENT_TYPES**


:   - Default:
    ```python
    ['doc', 'docx', 'gif', 'jpg', 'jpeg', 'ods', 'odt', 'odp', 'pdf', 'png',
    'ppt', 'pptx', 'rar', 'sld', 'tif', 'tiff', 'txt', 'xls', 'xlsx', 'xml',
    'zip', 'gz', 'qml']
    ```

A list of acceptable file extensions that can be uploaded to the Documents app.

**ANONYMOUS_USER_ID**


:   - Default ``-1``
    - Env: ``ANONYMOUS_USER_ID``

The id of an anonymous user. This is an django-guardian setting.

**API_INCLUDE_REGIONS_COUNT**


:   - Default ``False``
    - Env: ``API_INCLUDE_REGIONS_COUNT``

If set to ``True``, a counter with the total number of available regions will be added to the API JSON Serializer.

**API_LIMIT_PER_PAGE**


:   - Default ``200``
    - Env: ``API_LIMIT_PER_PAGE``

The Number of items returned by the APIs 0 equals no limit. Different from ``CLIENT_RESULTS_LIMIT``, affecting the number of items per page in the resource list.

**API_LOCKDOWN**


:   - Default ``True``
    - Env: ``API_LOCKDOWN``

If this is set to ``True`` users must be authenticated to get search results when search for for users, groups, categories, regions, tags etc.
Filtering search results of Resourcebase-objects like Layers, Maps or Documents by one of the above types does not work.
Attention: If API_LOCKDOWN is set to ``False`` all details can be accessed by anonymous users.

**ASYNC_SIGNALS**


:   - Default ``False``
    - Env: ``ACCOUNT_NOTIFY_ON_PASSWORD_CHANGE``

**AUTH_EXEMPT_URLS**


:   - Default:
    ```python
    (r'^/?$',
    '/gs/*',
    '/static/*',
    '/o/*',
    '/api/o/*',
    '/api/roles',
    '/api/adminRole',
    '/api/users',
    '/api/layers',)
    ```
A tuple of URL patterns that the user can visit without being authenticated.
This setting has no effect if ``LOCKDOWN_GEONODE`` is not True.  For example,
``AUTH_EXEMPT_URLS = ('/maps',)`` will allow unauthenticated users to
browse maps.

**AUTO_ASSIGN_REGISTERED_MEMBERS_TO_CONTRIBUTORS**


:   - Default ``True``
    - Env: ``AUTO_ASSIGN_REGISTERED_MEMBERS_TO_CONTRIBUTORS``

Assign **new** registered users to the contributors group. If set to `False` new registered members will not obtain automatic permissions to create and edit resources.

**AUTO_ASSIGN_REGISTERED_MEMBERS_TO_REGISTERED_MEMBERS_GROUP_NAME**


:   - Default ``True``
    - Env: ``AUTO_ASSIGN_REGISTERED_MEMBERS_TO_REGISTERED_MEMBERS_GROUP_NAME``

Auto assign users to a default ``REGISTERED_MEMBERS_GROUP_NAME`` private group after ``AUTO_ASSIGN_REGISTERED_MEMBERS_TO_REGISTERED_MEMBERS_GROUP_AT``.

**AUTO_ASSIGN_REGISTERED_MEMBERS_TO_REGISTERED_MEMBERS_GROUP_AT**


:   - Default ``activation``
    - Env: ``AUTO_ASSIGN_REGISTERED_MEMBERS_TO_REGISTERED_MEMBERS_GROUP_AT``
| Options: ``"registration" | "activation" | "login"``

Auto assign users to a default ``REGISTERED_MEMBERS_GROUP_NAME`` private group after {"registration" | "activation" | "login"}.

Notice that whenever ``ACCOUNT_EMAIL_VERIFICATION == True`` and ``ACCOUNT_APPROVAL_REQUIRED == False``, users will be able to register and they became ``active`` already, even if they won't be able to login until the email has been verified.

**AUTO_GENERATE_AVATAR_SIZES**


:   - Default ``20, 30, 32, 40, 50, 65, 70, 80, 100, 140, 200, 240``

An iterable of integers representing the sizes of avatars to generate on upload. This can save rendering time later on if you pre-generate the resized versions.

**AVATAR_GRAVATAR_SSL**


  | :   Default:  ``False``
      - Env: ``AVATAR_GRAVATAR_SSL``
  | Options: ``True | False``

  Force SSL when loading fallback image from gravatar.com.

**AVATAR_DEFAULT_URL**


  | :   Default:  ``/geonode/img/avatar.png``
      - Env: ``AVATAR_GRAVATAR_SSL``
  | Options: ``"filepath to image"``

  Allows to set a custom fallback image in case a User has not uploaded a profile image.
  Needs ``AVATAR_PROVIDERS`` to be set correctly.

**AVATAR_PROVIDERS**


  | Default:
```
'avatar.providers.PrimaryAvatarProvider','avatar.providers.GravatarAvatarProvider','avatar.providers.DefaultAvatarProvider'
```

      - Env: ``AVATAR_PROVIDERS``
  | Options: ``Avatar provider object``


  This setting configures in which order gravatar images are loaded. A common use case is the use of a local image over a fallback image loaded from gravatar.com.
  To do so you would change the order like:

```
'avatar.providers.PrimaryAvatarProvider','avatar.providers.DefaultAvatarProvider','avatar.providers.GravatarAvatarProvider'
```
  (DefaultAvatarProvider before GravatarAvatarProvider)


## B

**BING_API_KEY**


:   - Default ``None``
    - Env: ``BING_API_KEY``

This property allows to enable a Bing Aerial background.

If using ``mapstore`` client library, make sure the ``MAPSTORE_BASELAYERS`` include the following:

```python
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
```

## C

**CACHES**


:   - Default:
    ```python
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
    ```

A dictionary containing the settings for all caches to be used with Django.
This is a [Django setting](https://docs.djangoproject.com/en/3.2/ref/settings/#std:setting-CACHES)

The ``'default'`` cache is disabled because we don't have a mechanism to discriminate between client sessions right now, and we don't want all users fetch the same api results.

The ``'resources'`` is not currently used. It might be helpful for [caching Django template fragments](https://docs.djangoproject.com/en/3.2/topics/cache/#template-fragment-caching) and/or [Tastypie API Caching](https://django-tastypie.readthedocs.io/en/latest/caching.html).


**CACHE_BUSTING_STATIC_ENABLED**


:   - Default ``False``
    - Env: ``CACHE_BUSTING_STATIC_ENABLED``

This is a [Django Compressed Manifet storage provided by WhiteNoise](http://whitenoise.evans.io/en/stable/django.html#add-compression-and-caching-support)
A boolean allowing you to enable the ``WhiteNoise CompressedManifestStaticFilesStorage storage``. This works only on a production system.

.. warning:: This works only if ``DEBUG = False``


**CASCADE_WORKSPACE**


:   - Default ``geonode``
    - Env: ``CASCADE_WORKSPACE``


**CATALOGUE**


A dict with the following keys:

 ENGINE: The CSW backend (default is ``geonode.catalogue.backends.pycsw_local``)
 URL: The FULLY QUALIFIED base URL to the CSW instance for this GeoNode
 USERNAME: login credentials (if required)
 PASSWORD: login credentials (if required)

pycsw is the default CSW enabled in GeoNode. pycsw configuration directives
are managed in the PYCSW entry.

**CATALOGUE_METADATA_TEMPLATE**


Default : ``catalogue/full_metadata.xml``

A string with the catalogue xml file needed for the metadata.

**CATALOGUE_METADATA_XSL**


Default : ``'/static/metadataxsl/metadata.xsl``

A string pointing to the XSL used to transform the metadata XML into human readable HTML.

**CLIENT_RESULTS_LIMIT**


:   - Default ``5``
    - Env: ``CLIENT_RESULTS_LIMIT``

The Number of results per page listed in the GeoNode search pages. Different from ``API_LIMIT_PER_PAGE``, affecting the number of items returned by the APIs.

**CORS_ALLOW_ALL_ORIGINS**


:   - Default ``False``
    - Env: ``CORS_ALLOW_ALL_ORIGINS``

If set to true `Access-Control-Allow-Origin: *` header is set for any response. A safer option (not managed through env vars at the moment) is `CORS_ALLOWED_ORIGINS`, where a list of hosts can be configured, o `CORS_ALLOWED_ORIGIN_REGEXES`, where the list can contain regexes.
Notice that the Nginx in front of GeoNode always includes `Access-Control-Allow-Credentials true`. This must also taken into account when CORS is enabled. 

**CREATE_LAYER**


:   - Default ``False``
    - Env: ``CREATE_LAYER``

Enable the creaation of a new empty layer.

**CUSTOM_METADATA_SCHEMA**


:   - Default ``{}``

If present, will extend the available metadata schema used for store
new value for each resource. By default override the existing one.
The expected schema is the same as the default

## D

**DATA_UPLOAD_MAX_NUMBER_FIELDS**


:   Default:  ``100000``

Maximum value of parsed attributes.


**DATASET_DOWNLOAD_HANDLERS**


:   Default:  ``[]``

Additional download handlers that provides a link to download the resource

**DEBUG**


:   - Default ``False``
    - Env: ``DEBUG``

One of the main features of debug mode is the display of detailed error pages. If your app raises an exception when DEBUG is True, Django will display a detailed traceback, including a lot of metadata about your environment, such as all the currently defined Django settings (from settings.py).
This is a [Django Setting](https://docs.djangoproject.com/en/3.2/ref/settings/#debug)

[](){ #default-anonymous-download-permission }
**DEFAULT_ANONYMOUS_DOWNLOAD_PERMISSION**

:   Default:  ``True``

Whether the uploaded resources should downloadable by default.

[](){ #default-anonymous-view-permission }
**DEFAULT_ANONYMOUS_VIEW_PERMISSION**

:   Default:  ``True``

Whether the uploaded resources should be public by default.


**DEFAULT_DATASET_DOWNLOAD_HANDLER**


:   Default:  ``geonode.layers.download_handler.DatasetDownloadHandler``

from GeoNode 4.2.x has bee introduced with this issue #11296 and later improved with this issue #11421 
the concept of Download Handler and ofc GeoNode provides a default implementation of it
which process the download via WPS

**DEFAULT_EXTRA_METADATA_SCHEMA**


:   Default:
    ```json
    {
    Optional("id"): int,
    "filter_header": object,
    "field_name": object,
    "field_label": object,
    "field_value": object,
    }
    ```

Define the default metadata schema used for add to the resource extra metadata without modify the actual model.
This schema is used as validation for the input metadata provided by the user

- `id`: (optional int): the identifier of the metadata. Optional for creation, required in Upgrade phase
- `filter_header`: (required object): Can be any type, is used to generate the facet filter header. Is also an identifier.
- `field_name`: (required object): name of the metadata field
- `field_label`: (required object): verbose string of the name. Is used as a label in the facet filters.
- `field_value`: (required object): metadata values

An example of metadata that can be ingested is the follow:

```json
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
```


**DEFAULT_LAYER_FORMAT**


:   - Default ``image/png``
    - Env: ``DEFAULT_LAYER_FORMAT``

The default format for requested tile images.


**DEFAULT_MAP_CENTER**


:   - Default ``(0, 0)``
    - Env: ``DEFAULT_MAP_CENTER_X`` ``DEFAULT_MAP_CENTER_Y``

A 2-tuple with the latitude/longitude coordinates of the center-point to use
in newly created maps.

**DEFAULT_MAP_CRS**


:   - Default ``EPSG:3857``
    - Env: ``DEFAULT_MAP_CRS``

The default map projection. :   Default:  EPSG:3857

**DEFAULT_MAP_ZOOM**


:   - Default ``0``
    - Env: ``DEFAULT_MAP_ZOOM``

The zoom-level to use in newly created maps.  This works like the OpenLayers
zoom level setting; 0 is at the world extent and each additional level cuts
the viewport in half in each direction.

**DEFAULT_MAX_PARALLEL_UPLOADS_PER_USER**


:   Default:  ``5``

When [uploading datasets](../../usage/managing_datasets/uploading_datasets.html#datasets-uploading), 
this value limits the number os parallel uploads.

The parallelism limit is set during installation using the value of this variable.
After installation, only an user with administrative rights can change it.
These limits can be changed in the [admin panel](../../admin/upload-parallelism-limit/index.html#upload-parallelism-limit)
or [accessing by api](../../devel/api/V2/index.html#getapi-v2-upload-parallelism-limits-).



**DEFAULT_MAX_UPLOAD_SIZE**


:   Default:  ``104857600`` (100 MB in bytes)

When [uploading datasets](../../usage/managing_datasets/uploading_datasets.html#datasets-uploading)
or [uploading documents](../../usage/managing_documents/uploading_documents.html#uploading-documents),
the total size of the uploaded files is verified.

The size limits are set during installation using the value of this variable.
After installation, only an user with administrative rights can change it.
These limits can be changed in the [admin panel](../../admin/upload-size-limits/index.html#upload-size-limits)
or [accessing by api](../../devel/api/V2/index.html#getapi-v2-upload-size-limits-).


**DEFAULT_SEARCH_SIZE**


:   - Default ``10``
    - Env: ``DEFAULT_SEARCH_SIZE``

An integer that specifies the default search size when using ``geonode.search`` for querying data.

**DEFAULT_WORKSPACE**


:   - Default ``geonode``
    - Env: ``DEFAULT_WORKSPACE``

The standard GeoServer workspace.

**DISPLAY_WMS_LINKS**


:   - Default ``True``
    - Env: ``DISPLAY_WMS_LINKS``

If set to False direct WMS link to GeoServer is hidden.

**DISPLAY_ORIGINAL_DATASET_LINK**


:   - Default ``True``
    - Env: ``DISPLAY_ORIGINAL_DATASET_LINK``

If set to False original dataset download is hidden.

**DOWNLOAD_FORMATS_METADATA**

Specifies which metadata formats are available for users to download.

:   - Default:
    ```python
    DOWNLOAD_FORMATS_METADATA = [
    'Atom', 'DIF', 'Dublin Core', 'ebRIM', 'FGDC', 'ISO',
    ]
    ```

**DOWNLOAD_FORMATS_VECTOR**

Specifies which formats for vector data are available for users to download.

:   - Default:
    ```python
    DOWNLOAD_FORMATS_VECTOR = [
    'JPEG', 'PDF', 'PNG', 'Zipped Shapefile', 'GML 2.0', 'GML 3.1.1', 'CSV',
    'Excel', 'GeoJSON', 'KML', 'View in Google Earth', 'Tiles',
    ]
    ```

**DOWNLOAD_FORMATS_RASTER**

Specifies which formats for raster data are available for users to download.

:   - Default
    ```python
    DOWNLOAD_FORMATS_RASTER = [
    'JPEG', 'PDF', 'PNG' 'Tiles',
    ]
    ```

## E

**EMAIL_ENABLE**

:   - Default ``False``

Options:

- EMAIL_BACKEND - Default:  ``django.core.mail.backends.smtp.EmailBackend``
- EMAIL_HOST - Default:  ``localhost``
- EMAIL_PORT - Default:  ``25``
- EMAIL_HOST_USER -  Default:  ``''``
- EMAIL_HOST_PASSWORD - Default:  ``''``
- EMAIL_USE_TLS - Default:  ``False``
- EMAIL_USE_SSL - Default:  ``False``
- DEFAULT_FROM_EMAIL - Default:  ``GeoNode <no-reply@geonode.org>``

**EPSG_CODE_MATCHES**


:   - Default:
    ```python
    {
    'EPSG:4326': '(4326) WGS 84',
    'EPSG:900913': '(900913) Google Maps Global Mercator',
    'EPSG:3857': '(3857) WGS 84 / Pseudo-Mercator',
    'EPSG:3785': '(3785 DEPRECATED) Popular Visualization CRS / Mercator',
    'EPSG:32647': '(32647) WGS 84 / UTM zone 47N',
    'EPSG:32736': '(32736) WGS 84 / UTM zone 36S'
    }
    ```

Supported projections human readable descriptions associated to their EPSG Codes.
This list will be presented to the user during the upload process whenever GeoNode won't be able to recognize a suitable projection.
Those codes should be aligned to the `UPLOADER` ones and available in GeoServer also.

**EXTRA_METADATA_SCHEMA**


:   - Default:
    ```python
    EXTRA_METADATA_SCHEMA = {**{
    "map": os.getenv('MAP_EXTRA_METADATA_SCHEMA', DEFAULT_EXTRA_METADATA_SCHEMA),
    "layer": os.getenv('DATASET_EXTRA_METADATA_SCHEMA', DEFAULT_EXTRA_METADATA_SCHEMA),
    "document": os.getenv('DOCUMENT_EXTRA_METADATA_SCHEMA', DEFAULT_EXTRA_METADATA_SCHEMA),
    "geoapp": os.getenv('GEOAPP_EXTRA_METADATA_SCHEMA', DEFAULT_EXTRA_METADATA_SCHEMA)
    }, **CUSTOM_METADATA_SCHEMA}
    ```
Variable used to actually get the expected metadata schema for each resource_type.
In this way, each resource type can have a different metadata schema

## F

**FREETEXT_KEYWORDS_READONLY**


:   - Default ``False``
    - Env: ``FREETEXT_KEYWORDS_READONLY``

Make Free-Text Keywords writable from users. Or read-only when set to False.


**FACET_PROVIDERS**


:   - Default ``pre filled list of providers``
    - Env: ``FACET_PROVIDERS``

Contains the list of the providers available to perform an serve the facets. 
In case the user wants remove a facets, is enough to remove the path 
of the proider from the list


## G

**GEOSERVER_ADMIN_USER**


:   - Default ``admin``
    - Env: ``GEOSERVER_ADMIN_PASSWORD``

The geoserver admin username.

**GEOSERVER_ADMIN_PASSWORD**


:   - Default ``geoserver``
    - Env: ``GEOSERVER_ADMIN_USER``

The GeoServer admin password.

**GEOSERVER_LOCATION**


:   - Default ``http://localhost:8080/geoserver/``
    - Env: ``GEOSERVER_LOCATION``

Url under which GeoServer is available.

**GEOSERVER_PUBLIC_HOST**


:   - Default ``SITE_HOST_NAME`` (Variable)
    - Env: ``GEOSERVER_PUBLIC_HOST``

Public hostname under which GeoServer is available.

**GEOSERVER_PUBLIC_LOCATION**


:   - Default ``SITE_HOST_NAME`` (Variable)
    - Env: ``GEOSERVER_PUBLIC_LOCATION``

Public location under which GeoServer is available.

**GEOSERVER_PUBLIC_PORT**


:   - Default ``8080 (Variable)``
    - Env: ``GEOSERVER_PUBLIC_PORT``


Public Port under which GeoServer is available.

**GEOSERVER_WEB_UI_LOCATION**


:   - Default ``GEOSERVER_PUBLIC_LOCATION (Variable)``
    - Env: ``GEOSERVER_WEB_UI_LOCATION``

Public location under which GeoServer is available.

**GROUP_PRIVATE_RESOURCES**


:   - Default ``False``
    - Env: ``GROUP_PRIVATE_RESOURCES``

If this option is enabled, Resources belonging to a Group won't be visible by others

## I

**IMPORTER HANDLERS**


:   - Default ``pre filled list of handlers``
    - Env: ``IMPORTER_HANDLERS``

Contains the list of the handlers available to perform an import of a resource. 
In case the user wants to drop the support during the import phase, is enough to
remove the path of the Handler from the list

## L

**LOCKDOWN_GEONODE**


:   - Default ``False``
    - Env: ``LOCKDOWN_GEONODE``

By default, the GeoNode application allows visitors to view most pages without being authenticated. If this is set to ``True``
users must be authenticated before accessing URL routes not included in ``AUTH_EXEMPT_URLS``.

**LOGIN_URL**


:   - Default ``{}account/login/'.format(SITEURL)``
    - Env: ``LOGIN_URL``

The URL where requests are redirected for login.


**LOGOUT_URL**


:   - Default ``{}account/login/'.format(SITEURL)``
    - Env: ``LOGOUT_URL``

The URL where requests are redirected for logout.

## M

**MAPSTORE_BASELAYERS**


:   - Default

```python
[
    {
        "type": "osm",
        "title": "Open Street Map",
        "name": "mapnik",
        "source": "osm",
        "group": "background",
        "visibility": True
    }, 
    {
        "type": "tileprovider",
        "title": "OpenTopoMap",
        "provider": "OpenTopoMap",
        "name": "OpenTopoMap",
        "source": "OpenTopoMap",
        "group": "background",
        "visibility": False
    }, 
    {
        "type": "wms",
        "title": "Sentinel-2 cloudless - https://s2maps.eu",
        "format": "image/jpeg",
        "id": "s2cloudless",
        "name": "s2cloudless:s2cloudless",
        "url": "https://maps.geo-solutions.it/geoserver/wms",
        "group": "background",
        "thumbURL": "%sstatic/mapstorestyle/img/s2cloudless-s2cloudless.png" % SITEURL,
        "visibility": False
    }, 
    {
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
```

Allows to specify which backgrounds MapStore should use. The parameter ``visibility`` for a layer, specifies which one is the default one.

A sample configuration using the Bing background without OpenStreetMap, could be the following one:

```python
[
    {
        "type": "bing",
        "title": "Bing Aerial",
        "name": "AerialWithLabels",
        "source": "bing",
        "group": "background",
        "apiKey": "{{apiKey}}",
        "visibility": True
    }, 
    {
        "type": "tileprovider",
        "title": "OpenTopoMap",
        "provider": "OpenTopoMap",
        "name": "OpenTopoMap",
        "source": "OpenTopoMap",
        "group": "background",
        "visibility": False
    },
    {
        "type": "wms",
        "title": "Sentinel-2 cloudless - https://s2maps.eu",
        "format": "image/jpeg",
        "id": "s2cloudless",
        "name": "s2cloudless:s2cloudless",
        "url": "https://maps.geo-solutions.it/geoserver/wms",
        "group": "background",
        "thumbURL": "%sstatic/mapstorestyle/img/s2cloudless-s2cloudless.png" % SITEURL,
        "visibility": False
    },
    {
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
```
.. warning:: To use a Bing background, you need to correctly set and provide a valid ``BING_API_KEY``

**MAX_DOCUMENT_SIZE**


:   - Default``2``
    - Env: ``MAX_DOCUMENT_SIZE``

Allowed size for documents in MB.

**METADATA_PARSERS**

:   It's possible to define multiple XML parsers for ingest XML during the layer upload.

The variable should be declared in this way inside the `settings.py`:

`METADATA_PARSERS = ['list', 'of', 'parsing', 'functions']`

If you want to always use the default metadata parser and after use your own, the variable must be set with first value as `__DEFAULT__`
Example:

`METADATA_PARSERS = ['__DEFAULT__', 'custom_parsing_function]`

If not set, the system will use the `__DEFAULT__` parser.

The custom parsing function must be accept in input 6 parameter that are:

- `exml` (xmlfile)
- `uuid` (str)
- `vals` (dict)
- `regions` (list)
- `keywords` (list)
- `custom` (dict)

If you want to use your parser after the default one, here is how the variable are populated:

- `exml`: the XML file to parse
- `uuid`: the UUID of the layer
- `vals`: Dictionary of information that belong to ResourceBase
- `regions`: List of regions extracted from the XML
- `keywords`: List of dict of keywords already divided between free-text and thesarus
- `custom`: Custom varible

!!! Note
    the keywords must be in a specific format, since later this dict, will be ingested by the `KeywordHandler` which will assign the keywords/thesaurus to the layer.

```python
{
"keywords": [list_of_keyword_extracted],
"thesaurus": {"date": None, "datetype": None, "title": None}, # thesaurus informations
"type": theme,  #extracted theme if present
}
```
Here is an example of expected parser function

```python
def custom_parsing_function(exml, uuid, vals, regions, keywords, custom):
# Place here your code
return uuid, vals, regions, keywords, custom
```
For more information, please rely to `TestCustomMetadataParser` which contain a smoke test to explain the functionality


**METADATA_STORERS**

:   Is possible to define multiple Layer storer during the layer upload.

The variable should be declared in this way:

`METADATA_STORERS = ['custom_storer_function']`

NOTE: By default the Layer is always saved with the default behaviour.

The custom storer function must be accept 2 input parameter that are:

- `layer` (layer model instance)
- `custom` (dict)

Here is how the variable are populated by default:

- `layer`: (layer model instance) that we wanto to change
- `custom`: custom dict populated by the parser

Here is an example of expected storer function

```python
def custom_storer_function(layer, custom):
# do something here
pass
```

For more information, please rely to `TestMetadataStorers` which contain a smoke test to explain the functionality


**MISSING_THUMBNAIL**


:   Default:  ``geonode/img/missing_thumb.png``

The path to an image used as thumbnail placeholder.


**MEMCACHED_BACKEND**

:   Default:  ``django.core.cache.backends.memcached.PyMemcacheCache``

Define which backend of memcached will be used


**MEMCACHED_ENABLED**

:   Default:  ``False``

If True, will use MEMCACHED_BACKEND as default backend in CACHES


**MODIFY_TOPICCATEGORY**


:   Default:  ``False``

Metadata Topic Categories list should not be modified, as it is strictly defined
by ISO (See: http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml
and check the <CodeListDictionary gml:id="MD_MD_TopicCategoryCode"> element).

Some customization is still possible changing the is_choice and the GeoNode
description fields.

In case it is necessary to add/delete/update categories, it is
possible to set the MODIFY_TOPICCATEGORY setting to True.

## N

**NOTIFICATION_ENABLED**


:   - Default ``True``
    - Env: ``NOTIFICATION_ENABLED``

Enable or disable the notification system.

## P

**PROXY_ALLOWED_HOSTS**


:   Default:  `()` (Empty tuple)

A tuple of strings representing the host/domain names that GeoNode can proxy requests to. This is a security measure
to prevent an attacker from using the GeoNode proxy to render malicious code or access internal sites.

Values in this tuple can be fully qualified names (e.g. 'www.geonode.org'), in which case they will be matched against
the request’s Host header exactly (case-insensitive, not including port). A value beginning with a period can be used
as a subdomain wildcard: `.geonode.org` will match `geonode.org`, `www.geonode.org`, and any other subdomain of
geonode.org. A value of '*' will match anything and is not recommended for production deployments.


**PROXY_URL**


:   Default: ``/proxy/?url=``

The URL to a proxy that will be used when making client-side requests in GeoNode.  By default, the
internal GeoNode proxy is used but administrators may favor using their own, less restrictive proxies.


**PYCSW**


:   A dict with pycsw's configuration with two possible keys CONFIGURATION and FILTER.

`CONFIGURATION`: Of note are the sections ``metadata:main`` to set CSW server metadata and ``metadata:inspire``
to set INSPIRE options.  Setting ``metadata:inspire['enabled']`` to ``true``
will enable INSPIRE support.   Server level configurations can be overridden
in the ``server`` section.  See http://docs.pycsw.org/en/latest/configuration.html
for full pycsw configuration details.

`FILTER`: Optional settings in order to add a filter to the CSW filtering.
The filter follow the django orm structure and must be a `ResourceBase` field/related field.
By default CSW will filter only for `layer` resource_type

Example of PYCSW configuration.
```python
PYCSW: {
    'CONFIGURATION': {...},
    'FILTER': {'resource_type__in':['layer'] }
}
```

## R

**RECAPTCHA_ENABLED**

:   - Default ``False``
    - Env: ``RECAPTCHA_ENABLED``

Allows enabling reCaptcha field on signup form.
Valid Captcha Public and Private keys will be needed as specified here https://pypi.org/project/django-recaptcha/#installation

You will need to generate a keys pair for ``reCaptcha v2`` for your domain from https://www.google.com/recaptcha/admin/create


**RECAPTCHA_PUBLIC_KEY**

:   - Default ``geonode_RECAPTCHA_PUBLIC_KEY``
    - Env: ``RECAPTCHA_PUBLIC_KEY``

You will need to generate a keys pair for ``reCaptcha v2`` for your domain from https://www.google.com/recaptcha/admin/create

**RECAPTCHA_PRIVATE_KEY**


:   - Default ``geonode_RECAPTCHA_PRIVATE_KEY``
    - Env: ``RECAPTCHA_PRIVATE_KEY``

You will need to generate a keys pair for ``reCaptcha v2`` for your domain from https://www.google.com/recaptcha/admin/create


**REGISTERED_MEMBERS_GROUP_NAME**

:   - Default ``registered-members``
    - Env: ``REGISTERED_MEMBERS_GROUP_NAME``

Used by ``AUTO_ASSIGN_REGISTERED_MEMBERS_TO_REGISTERED_MEMBERS_GROUP_NAME`` settings.

**REGISTERED_MEMBERS_GROUP_TITLE**


:   - Default ``Registered Members``
    - Env: ``REGISTERED_MEMBERS_GROUP_TITLE``

Used by ``AUTO_ASSIGN_REGISTERED_MEMBERS_TO_REGISTERED_MEMBERS_GROUP_NAME`` settings.

**REGISTRATION_OPEN**


:   Default:  ``False``

A boolean that specifies whether users can self-register for an account on your site.

**RESOURCE_PUBLISHING**


:   Default:  ``False``

By default, the GeoNode application allows GeoNode staff members to
publish/unpublish resources.
By default, resources are published when created. When this setting is set to
True the staff members will be able to unpublish a resource (and eventually
publish it back).

## S

**SEARCH_FILTERS**


:   - Default;
        - `TEXT_ENABLED`: `True`,
        - `TYPE_ENABLED`: `True`,
        - `CATEGORIES_ENABLED`: `True`,
        - `OWNERS_ENABLED`: `True`,
        - `KEYWORDS_ENABLED`: `True`,
        - `H_KEYWORDS_ENABLED`: `True`,
        - `T_KEYWORDS_ENABLED`: `True`,
        - `DATE_ENABLED`: `True`,
        - `REGION_ENABLED`: `True`,
        - `EXTENT_ENABLED`: `True`,

Enabled Search Filters for filtering resources.


**SERVICES_TYPE_MODULES**

:   It's possible to define multiple Service Types Modules for custom service type with it's own Handler.

The variable should be declared in this way in `settings.py`:

`SERVICES_TYPE_MODULES = [ 'path.to.module1','path.to.module2', ... ]`

Default service types are already included

Inside each module in the list we need to define a variable:

```python
"services_type" = {
    "<key_of_service_type>": {
    "OWS": True/False,
    "handler": "<path.to.Handler>",
    "label": "<label to show in remote service page>",
    "management_view": "<path.to.view>"
}
}
```

the `key_of_service_type` is just an identifier to assign at the service type.
`OWS` is True if the service type is an OGC Service Compliant.
The `handler` key must contain the path to the class who will provide all methods to manage the service type
The `label` is what is shown in the service form when adding a new service.
The `management_view`, if exists, must contain the path to the method where the management page is opened.

**SERVICE_UPDATE_INTERVAL**


:   - Default ``0``

The Interval services are updated.

**SHOW_PROFILE_EMAIL**


:   Default:  ``False``

A boolean which specifies whether to display the email in the user’s profile.

**SITE_HOST_NAME**


:   - Default ``localhost``
    - Env: ``SITE_HOST_NAME``

The hostname used for GeoNode.

**SITE_HOST_PORT**


:   - Default ``8000``
    - Env: ``SITE_HOST_PORT``

The Site hostport.

**SITEURL**


:   Default:  ``'http://localhost:8000/'``

A base URL for use in creating absolute links to Django views and generating links in metadata.

**SIZE_RESTRICTED_FILE_UPLOAD_ELEGIBLE_URL_NAMES**


:   Default:  ``'("data_upload", "uploads-upload", "document_upload",)'``

Rappresent the list of the urls basename that are under file_size restriction

**SOCIALACCOUNT_AUTO_SIGNUP**


:   Default:  ``True``

Attempt to bypass the signup form by using fields (e.g. username, email) retrieved from the social account provider.
This is a [Django-allauth setting](https://django-allauth.readthedocs.io/en/latest/configuration.html)


**SOCIALACCOUNT_WITH_GEONODE_LOCAL_SINGUP**


:   Default:  ``True``

Variable which controls displaying local account registration form. By default form is visible


**SEARCH_RESOURCES_EXTENDED**


:   Default:  ``True``

This will extend search with additinoal properties. By default its on and search engine will check resource title or purpose or abstract.
When set to False just title lookup is performed.

**SUPPORTED_DATASET_FILE_TYPES**


:   - Default:
    ```python
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
    ```

Rappresent the list of the supported file type in geonode that can be ingested by the platform

For example. the following configuration is needed to add the GeoJSON as supported file:

```python
{
"id": "geojson",
"label": "GeoJSON",
"format": "metadata",
"ext": ["geojson"],
"mimeType": ["application/json"]
}
 ```

## T

**THEME_ACCOUNT_CONTACT_EMAIL**


:   Default:  ``'admin@example.com'``

This email address is added to the bottom of the password reset page in case users have trouble unlocking their account.

**THESAURI**


Default = ``[]``

A list of Keywords thesauri settings:
For example `THESAURI = [{'name':'inspire_themes', 'required':True, 'filter':True}, {'name':'inspire_concepts', 'filter':True}, ]`


## U

**USER_DELETION_RULES**

:   - Default ``["geonode.people.utils.user_has_resources"]``
    - Env: ``USER_DELETION_RULES``

List of callables that will be called the deletion of a user account is requested.
The deletion will fail if any of the callables return ``False``. 
New rules can be added, as a string path to the callable, as long as they take as parameter
the user object and return a boolean.


**UUID HANDLER**

Is possible to define an own uuidhandler for the Layer.

To start using your own handler, is needed to add the following configuration:

`LAYER_UUID_HANDLER = "mymodule.myfile.MyObject"`

The Object must accept as `init` the `instance` of the layer and have a method named `create_uuid()`

here is an example:

```python
class MyObject():
    def __init__(self, instance):
        self.instance = instance
    def create_uuid(self):
    # here your code
    pass
```

## X

**X_FRAME_OPTIONS**

:   Default:  ``'ALLOW-FROM %s' % SITEURL``

This is a [Django setting](https://docs.djangoproject.com/en/3.2/ref/clickjacking/#setting-x-frame-options-for-all-responses)
