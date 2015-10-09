.. _settings:

========
Settings
========

Here’s a list of settings available in GeoNode and their default values.  This includes settings for some external applications that
GeoNode depends on.

.. comment:
    :local:
    :depth: 1

Documents settings
==================

Here's a list of settings available for the Documents app in GeoNode.

ALLOWED_DOCUMENT_TYPES
----------------------
Default: ``['doc', 'docx', 'xls', 'xlsx', 'pdf', 'zip', 'jpg', 'jpeg', 'tif', 'tiff', 'png', 'gif', 'txt']``

A list of acceptable file extensions that can be uploaded to the Documents app.

MAX_DOCUMENT_SIZE
-----------------
Default: ``2``

Metadata settings
=================
  
CATALOGUE
---------
A dict with the following keys:

* ENGINE: The CSW backend (default is ``geonode.catalogue.backends.pycsw_local``)
* URL: The FULLY QUALIFIED base url to the CSW instance for this GeoNode
* USERNAME: login credentials (if required)
* PASSWORD: login credentials (if required)

pycsw is the default CSW enabled in GeoNode.  pycsw configuration directives
are managed in the PYCSW entry.

PYCSW
-----
  A dict with pycsw's configuration.  Of note are the sections
  ``metadata:main`` to set CSW server metadata and ``metadata:inspire``
  to set INSPIRE options.  Setting ``metadata:inspire['enabled']`` to ``true``
  will enable INSPIRE support.   Server level configurations can be overridden
  in the ``server`` section.  See http://docs.pycsw.org/en/latest/configuration.html
  for full pycsw configuration details.
  
DEFAULT_TOPICCATEGORY
---------------------
Default: ``'location'``

The identifier of the default topic category to use when uploading new layers.  The value specified for this setting must be
present in the TopicCategory table or GeoNode will return a ``TopicCategory.DoesNotExist`` exception.

MODIFY_TOPICCATEGORY
--------------------
Default: ``False``

Metadata Topic Categories list should not be modified, as it is strictly defined
by ISO (See: http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml 
and check the <CodeListDictionary gml:id="MD_MD_TopicCategoryCode"> element).

Some customisation it is still possible changing the is_choice and the GeoNode 
description fields.

In case it is absolutely necessary to add/delete/update categories, it is
possible to set the MODIFY_TOPICCATEGORY setting to True.

Maps settings
=============

DEFAULT_MAP_BASE_LAYER
----------------------
The name of the background layer to include in newly created maps.

DEFAULT_MAP_CENTER
------------------
Default: ``(0, 0)``

A 2-tuple with the latitude/longitude coordinates of the center-point to use
in newly created maps.

DEFAULT_MAP_ZOOM
----------------
Default: ``0``

The zoom-level to use in newly created maps.  This works like the OpenLayers
zoom level setting; 0 is at the world extent and each additional level cuts
the viewport in half in each direction.

MAP_BASELAYERS
--------------
Default::


    MAP_BASELAYERS = [{
    "source": {
        "ptype": "gxp_wmscsource",
        "url": OGC_SERVER['default']['PUBLIC_LOCATION'] + "wms",
        "restUrl": "/gs/rest"
     }
      },{
        "source": {"ptype": "gxp_olsource"},
        "type":"OpenLayers.Layer",
        "args":["No background"],
        "visibility": False,
        "fixed": True,
        "group":"background"
      }, {
        "source": {"ptype": "gxp_osmsource"},
        "type":"OpenLayers.Layer.OSM",
        "name":"mapnik",
        "visibility": False,
        "fixed": True,
        "group":"background"
      }, {
        "source": {"ptype": "gxp_mapquestsource"},
        "name":"osm",
        "group":"background",
        "visibility": True
      }, {
        "source": {"ptype": "gxp_mapquestsource"},
        "name":"naip",
        "group":"background",
        "visibility": False
      }, {
        "source": {"ptype": "gxp_bingsource"},
        "name": "AerialWithLabels",
        "fixed": True,
        "visibility": False,
        "group":"background"
      },{
        "source": {"ptype": "gxp_mapboxsource"},
      }, {
        "source": {"ptype": "gxp_olsource"},
        "type":"OpenLayers.Layer.WMS",
        "group":"background",
        "visibility": False,
        "fixed": True,
        "args":[
          "bluemarble",
          "http://maps.opengeo.org/geowebcache/service/wms",
          {
            "layers":["bluemarble"],
            "format":"image/png",
            "tiled": True,
            "tilesOrigin": [-20037508.34, -20037508.34]
          },
          {"buffer": 0}
        ]

    }]

A list of dictionaries that specify the default map layers.

LAYER_PREVIEW_LIBRARY
---------------------
Default:  ``"leaflet"``

The library to use for display preview images of layers.  The library choices are:

* ``"leaflet"``
* ``"geoext"``

OGC_SERVER
----------
Default: ``{}`` (Empty dictionary)

A dictionary of OGC servers and and their options.  The main
server should be listed in the 'default' key.  If there is no 'default'
key or if the ``OGC_SERVER`` setting does not exist Geonode will raise
an Improperly Configured exception.  Below is an example of the ``OGC_SERVER``
setting::

   OGC_SERVER = {
     'default' : {
         'LOCATION' : 'http://localhost:8080/geoserver/',
         'USER' : 'admin',
         'PASSWORD' : 'geoserver',
     }
   }

BACKEND
.......
Default: ``"geonode.geoserver"``

The OGC server backend to use.  The backend choices are:

* ``'geonode.geoserver'``

BACKEND_WRITE_ENABLED
.....................
Default: ``True``

Specifies whether the OGC server can be written to.  If False, actions that modify
data on the OGC server will not execute.

DATASTORE
.........
Default: ``''`` (Empty string)

An optional string that represents the name of a vector datastore that Geonode uploads
are imported into.  In order to support vector datastore imports there also needs to be an
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

GEOGIG_ENABLED
..............
Default: ``False``

A boolean that represents whether the OGC server supports GeoGig datastores.

GEONODE_SECURITY_ENABLED
........................
Default: ``True``

A boolean that represents whether Geonode's security application is enabled.

LOCATION
........
Default: ``"http://localhost:8080/geoserver/"``

A base URL from which GeoNode can construct OGC service URLs.
If using Geoserver you can determine this by
visiting the GeoServer administration home page without the
/web/ at the end.  For example, if your GeoServer administration app is at
http://example.com/geoserver/web/, your server's location is http://example.com/geoserver.

MAPFISH_PRINT_ENABLED
.....................
Default: ``True``

A boolean that represents whether the Mapfish printing extension is enabled on the server.

PASSWORD
........
Default: ``'geoserver'``

The administrative password for the OGC server as a string.

PRINT_NG_ENABLED
................
Default: ``True``

A boolean that represents whether printing of maps and layers is enabled.


PUBLIC_LOCATION
...............
Default: ``"http://localhost:8080/geoserver/"``

The URL used to in most public requests from Geonode.  This settings allows a user to write to one OGC server (the LOCATION setting)
and read from a seperate server or the PUBLIC_LOCATION.

USER
....
Default: ``'admin'``

The administrative username for the OGC server as a string.

WMST_ENABLED
............
Default: ``False``

Not implemented.

WPS_ENABLED
...........
Default: ``False``

Not implemented.

TIMEOUT
.......
Default: ``10``

The maximum time, in seconds, to wait for the server to respond.

SITEURL
-------
Default: ``'http://localhost:8000/'``

A base URL for use in creating absolute links to Django views and generating links in metadata.

Proxy settings
==============

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

The url to a proxy that will be used when making client-side requests in GeoNode.  By default, the
internal GeoNode proxy is used but administrators may favor using their own, less restrictive proxies.

Search settings
===============

DEFAULT_SEARCH_SIZE
-------------------
Default: ``10``

An integer that specifies the default search size when using ``geonode.search`` for querying data.

Security settings
=================

AUTH_EXEMPT_URLS
----------------
Default: ``()`` (Empty tuple)

A tuple of url patterns that the user can visit without being authenticated.
This setting has no effect if ``LOCKDOWN_GEONODE`` is not True.  For example,
``AUTH_EXEMPT_URLS = ('/maps',)`` will allow unauthenticated users to
browse maps.

LOCKDOWN_GEONODE
----------------
Default: ``False``

By default, the GeoNode application allows visitors to view most pages without being authenticated. If this is set to ``True``
users must be authenticated before accessing URL routes not included in ``AUTH_EXEMPT_URLS``.

RESOURCE_PUBLISHING
-------------------
Default: ``True``

By default, the GeoNode application allows GeoNode staff members to 
publish/unpublish resources.
By default resources are published when created. When this settings is set to 
True the staff members will be able to unpublish a resource (and eventually 
publish it back).

Social settings
===============

SOCIAL_BUTTONS
--------------
Default: ``True``

A boolean which specifies whether the social media icons and javascript should be rendered in GeoNode.

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

A list of dictionaries that is used to generate the social links displayed in the Share tab.  For each origin, the name and and url format parameters are replaced by the actual values of the ResourceBase object (layer, map, document).

CKAN_ORIGINS
--------------
Default::

    CKAN_ORIGINS = [{
        "label":"Humanitarian Data Exchange (HDX)",
        "url":"https://data.hdx.rwlabs.org/dataset/new?title={name}&notes={abstract}",
        "css_class":"hdx"
    }]

A list of dictionaries that is used to generate the links to CKAN instances displayed in the Share tab.  For each origin, the name and and abstract format parameters are replaced by the actual values of the ResourceBase object (layer, map, document).  This is not enabled by default.  To enabled, uncomment the following line: SOCIAL_ORIGINS.extend(CKAN_ORIGINS).

TWITTER_CARD
--------------
Default:: ``True``

A boolean that specifies whether Twitter cards are enabled.

TWITTER_SITE
--------------
Default:: ``'@GeoNode'``

A string that specifies the site to for the twitter:site meta tag for Twitter Cards.

TWITTER_HASHTAGS
--------------
Default:: ``['geonode']``

A list that specifies the hastags to use when sharing a resource when clicking on a social link.

OPENGRAPH_ENABLED
--------------
Default:: ``True``

A boolean that specifies whether Open Graph is enabled.  Open Graph is used by Facebook and Slack.

Upload settings
===============

GEOGIG_DATASTORE_NAME
---------------------
Default: ``None``

A string with the default GeoGig datastore name.  This value is only used if no GeoGig datastore name is provided
when data is uploaded but it must be populated if your deployment supports GeoGig.

UPLOADER
--------
Default::

    {
        'BACKEND' : 'geonode.rest',
        'OPTIONS' : {
            'TIME_ENABLED': False,
            'GEOGIG_ENABLED': False,
        }
    }

A dictionary of Uploader settings and and their values.

BACKEND
.......
Default: ``'geonode.rest'``

The uploader backend to use.  The backend choices are:

* ``'geonode.importer'``
* ``'geonode.rest'``

The importer backend requires the Geoserver importer extension to be enabled and is required for uploading data into
GeoGig datastores.

OPTIONS
-------
Default::

    'OPTIONS' : {
        'TIME_ENABLED': False,
        'GEOGIG_ENABLED': False,
    }

TIME_ENABED
...........
Default: ``False``

A boolean that specifies whether the upload should allow the user to enable time support when uploading data.

GEOGIG_ENABED
.............
Default: ``False``

A boolean that specifies whether the uploader should allow the user to upload data into a GeoGig datastore.

User Account settings
=====================

REGISTRATION_OPEN
-----------------
Default: ``False``

A boolean that specifies whether users can self-register for an account on your site.

THEME_ACCOUNT_CONTACT_EMAIL
---------------------------
Default: ``'admin@example.com'``

This email address is added to the bottom of the password reset page in case users have trouble un-locking their account.

Download settings
=================

DOWNLOAD_FORMATS_METADATA
-------------------------

Specifies which metadata formats are available for users to download. 

Default::

    DOWNLOAD_FORMATS_METADATA = [
        'Atom', 'DIF', 'Dublin Core', 'ebRIM', 'FGDC', 'ISO',
    ]
    
DOWNLOAD_FORMATS_VECTOR
-------------------------

Specifies which formats for vector data are available for users to download. 

Default::

    DOWNLOAD_FORMATS_VECTOR = [
        'JPEG', 'PDF', 'PNG', 'Zipped Shapefile', 'GML 2.0', 'GML 3.1.1', 'CSV', 
        'Excel', 'GeoJSON', 'KML', 'View in Google Earth', 'Tiles',
    ]
    
DOWNLOAD_FORMATS_RASTER
-------------------------

Specifies which formats for raster data are available for users to download. 

Default::

    DOWNLOAD_FORMATS_RASTER = [
        'JPEG', 'PDF', 'PNG' 'Tiles',
    ]

Contrib settings
=================

EXIF_ENABED
...........
Default: ``False``

A boolean that specifies whether the Exif contrib app is enabled.  If enabled, metadata is generated from Exif tags when documents are uploaded.

NLP_ENABED
...........
Default: ``False``

A boolean that specifies whether the NLP (Natural Language Processing) contrib app is enabled.  If enabled, NLP (specifically MITIE) is used to infer additional metadata from uploaded documents to help fill metadata gaps.

NLP_LOCATION_THRESHOLD
-------------------
Default: ``1.0``

A float that specifies the threshold for location matches.

NLP_LIBRARY_PATH
--------------
Default:: ``'/opt/MITIE/mitielib'``

A string that specifies the location of the MITIE library

NLP_MODEL_PATH
--------------
Default:: ``'/opt/MITIE/MITIE-models/english/ner_model.dat'``

A string that specifies the location of the NER (Named Entity Resolver).  MITIE comes with English and Spanish NER models.  Other models can be trained.

SLACK_ENABED
...........
Default: ``False``

A boolean that specifies whether the Slack contrib app is enabled.  If enabled, GeoNode will send messages to the slack channels specified in SLACK_WEBHOOK_URLS when a document is uploaded, metadata is updated, etc.  Coverage of events is still incomplete.

SLACK_WEBHOOK_URLS
-------------------------

A list that specifies the urls to post Slack messages to.  Each url is for a different channel.  The default url should be replaced when slack integration is enabled.

Default::

    SLACK_WEBHOOK_URLS = [
        "https://hooks.slack.com/services/T000/B000/XX"
    ]

