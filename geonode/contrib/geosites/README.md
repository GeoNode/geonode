===============================
GeoSites: Multi-Tenancy GeoNode
===============================

GeoSites is a contrib module to GeoNode starting with 2.4. The GeoSites app is a way to run multiple websites with a single instance of GeoNode. Each GeoSite can have different templates, applications, and data permissions but share a single database, web mapping service (GeoServer), and CSW (pycsw).  This is useful when multiple websites are desired to support different sets of users, but with a similar set of data and overall look and feel of the sites.  Users can be given permission to access multiple sites if needed, which also allows administrative groups can be set up to support all sites with one account.

A GeoSites installation uses a 'master' GeoNode website that has access to all users, groups, and data. Through the Django admin page, Layers, Maps, Documents, Users, and Groups can be added and removed from all sites.  Users can be given access to any number of sites, and data may appear on only a single site, or all of them.  The master site need not be accessible from the outside so that it can be used as an internal tool to the organization. Users created on a site are created with access to just that site (but not the master site).  Data uploaded to a site is given permission on that site as well as the master site.


GeoSites Contrib App
============================

The GeoSites contrib app makes full use of the Django Site framework to separate the content between different GeoNode sites.
The Association of a resource to a site is done through a OneToMany table named “SiteResources” (a record for each site).
The table has two fields:
* site: a one to one relation with the Django Site
* resources: a many to many relation to the GeoNode ResourceBase model

This table is used by GeoSites to filter the resources per site. GeoSites also overrides all GeoNode data related endpoints (e.g., APIs, detail page, faceting facilities) to provide full multiple site support. Signals (post_save, post_delete) are used to ensure that when a Resource (layer, map, document) is saved (or deleted) it is added (or removed) to the SiteResource entry for the current site and for the Master site.


GeoSites Project
============================
A GeoSites project looks similar to a normal GeoNode project, but with additional folders for sites, and more settings files. In the project there is a directory for each site: 'master' and 'site2' in the example listing below. Each site folder contains a settings file (and optionally local_settings) with site specific settings, as well as directories for static files and Django templates. In addition are configuration files necessary to serve the site: nginx, gunicorn, and wsgi.py. GeoSites works via a hierarchy: first default GeoNode, then GeoSites settings, then project settings, then site specific settings. This hierachy is used for settings, templates, and static files.

The project_name folder contains common settings in the pre_settings.py, post_settings.py, and optionally local_settings.py files.  There is also a sites.json file, which is a JSON file of the sites database table.  This is for convenience, as the file will contain the site IDs and names for all currently enabled sites.  The urls file is a common urls file, although each site could have their own urls file if needed (by creating one and setting it in the site specific settings file).

The top level directory contains two manage scripts, and a typical setup script. The familiar manage.py is a regular Django manage file that uses the master site for the settings file. This is the command that should be used when doing many tasks such as inspecting the database, creating a super-user, or adding a new site.  The manage_all.py script is when a command should be run on all sites, syncdb and collectstatic being the common ones.  The syncdb command will call sync the DB to the settings file of each site, while collectstatic will loop through the sites and collect the static files of all sites in the common location they are served from.

~~~
geosites-project
├── project_name
│   ├── __init__.py
│   ├── local_settings.py
│   ├── master
│   │   ├── conf
│   │   │   ├── gunicorn
│   │   │   └── nginx
│   │   ├── __init__.py
│   │   ├── local_settings.py
│   │   ├── settings.py
│   │   ├── static
│   │   │   ├── css
│   │   │   │   └── site_base.css
│   │   │   ├── img
│   │   │   │   └── README
│   │   │   ├── js
│   │   │   │   └── README
│   │   │   └── README
│   │   ├── templates
│   │   │   ├── site_base.html
│   │   │   ├── site_index.html
│   │   └── wsgi.py
│   ├── post_settings.py
│   ├── pre_settings.py
│   ├── site2
│   │   ├── conf
│   │   │   ├── gunicorn
│   │   │   └── nginx
│   │   ├── __init__.py
│   │   ├── local_settings.py
│   │   ├── settings.py
│   │   ├── static
│   │   │   ├── css
│   │   │   │   └── site_base.css
│   │   │   ├── img
│   │   │   │   └── README
│   │   │   ├── js
│   │   │   │   └── README
│   │   │   └── README
│   │   ├── templates
│   │   │   ├── site_base.html
│   │   │   ├── site_index.html
│   │   └── wsgi.py
│   ├── sites.json
│   └── urls.py
├── manage_all.py
├── manage.py
├── README.rst
└── setup.py
~~~

Settings
============================
Site settings are managed through the use of common settings files as well as site specific settings files.   A simple site settings file looks like this:

~~~
import os
from geonode.contrib import geosites

# Read in GeoSites pre_settings
GEOSITES_ROOT = os.path.dirname(geosites.__file__)
execfile(os.path.join(GEOSITES_ROOT, 'pre_settings.py'))

# Site specific variables
SITE_ID = $SITE_ID
SITE_NAME = '$SITE_NAME'
SECRET_KEY = "fbk3CC3N6jt1AU9mGIcI"
SITE_APPS = ()
SITE_DATABASES = {}

# Overrides - common settings that might be overridden for site

# urls for all sites
# ROOT_URLCONF = 'projectname.urls'

# admin email
# THEME_ACCOUNT_CONTACT_EMAIL = ''

# Have GeoServer use this database for this site
# DATASTORE = ''

# Allow users to register
# REGISTRATION_OPEN = True

# Read in GeoSites post_settings
execfile(os.path.join(GEOSITES_ROOT, 'post_settings.py'))
~~~

This settings file first reads in the GeoSites pre_settings.py file, which in turns reads in the default GeoNode settings then overrides some of the values.  Then, site specific variables are set: the site ID, name, and secret key.  SITE_APPS are additional apps that should be added to this site, while SITE_DATABASES is used when a site should be using a separate database (such as for a datastore of geospatial data separate from other sites).  In this case add a geospatial DB to the SITE_DATABASES dictionary (or in the local_settings, see below), then set DATASTORE to the key of that database.

While Django apps on other sites are not automatically added, for single site administration they can be added to the master site through the master site settings.py file. 


##### Local Settings

Databases are usually set in a local_settings file, as are other production settings.  The local_settings file in the project directory is used by all sites, so it is here where the database is set for all sites.

~~~
# path for static and uploaded files
# SERVE_PATH = ''

"""
DATABASES = {
    'default' : {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': '',
        'USER' : '',
        'PASSWORD' : '',
        'HOST' : 'localhost',
        'PORT' : '5432',
    }
    # vector datastore for uploads
    # 'datastore' : {
    #    'ENGINE': 'django.contrib.gis.db.backends.postgis',
    #    'NAME': '',
    #    'USER' : '',
    #    'PASSWORD' : '',
    #    'HOST' : '',
    #    'PORT' : '',
    # }
}
"""

GEOSERVER_URL = 'http://localhost:8080/'
~~~

SERVE_PATH is the path used for serving of static files for all sites (it is also where webserver logs will be put). DATABASES are any production databases used by all sites. In the example above there is a database for the Django database, and another used for storing geospatial vector data served by GeoServer.  The GEOSERVER_URL is the internal URL (not the reverse proxy URL) of GeoServer, localhost port 8080 if running on the same machine.

Specific sites must also have a local_settings file in production environments.  This sets the SITEURL, as well as fixes the location of GeoServer for production.

~~~
import os

# Outside URL
SITEURL = 'http://$DOMAIN'

# databases unique to site if not defined in site settings
"""
SITE_DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(PROJECT_ROOT, '../development.db'),
    },
}
"""
~~~


Web and Application Servers
=====================
Created GeoSites have configuration files for nginx (as the web server) and gunicorn (as the application server).  While Apache config files (with mod_wsgi as the application server) are not currently genererated, Apache supports the same configuration necessary for GeoSites to work.

A single GeoServer instance is used to serve data to all of the GeoSites.  Each site proxies the /geoserver URL to the internal address of GeoServer.  The default GeoNode installation sets the URL of the GeoNode site in one of the GeoServer config files: GEOSERVER_DATA_DIR/security/auth/geonodeAuthProvider/config.xml  Change the baseUrl field to an empty string:

    <baseUrl></baseUrl>

When baseUrl is empty, GeoServer will attempt to authenticate against the requesting URL.  Since a reverse proxy to GeoServer is configured on the web servers the requesting URL can be used to determine the URL to GeoNode.

Databases
=====================
The master site, and all of the individual GeoSites, share a single database in a normal GeoSites setup. Objects, including users, groups, and data layers, all appear within the database but an additional sites table indicates which objects have access to which sites.  The geospatial data served by GeoServer (e.g., from PostGIS) can exist in the database like normal, since GeoServer will authenticate against the correct site, which will use it's database to determine permissions based on the object, current user, and site.


#### Adding New Sites

A management command exists to easily create a new site.  This will create all the needed directories, as well as a site specific settings file.  The command may also create a website configuration file.

    $ python manage.py addsite sitename sitedomain
    # example
    $ python manage.py addsite site3 site3.example.com

This will create a new directory of files:
~~~
│   ├── site3
│   │   ├── conf
│   │   │   ├── gunicorn
│   │   │   └── nginx
│   │   ├── __init__.py
│   │   ├── local_settings.py
│   │   ├── settings.py
│   │   ├── static
│   │   │   ├── css
│   │   │   │   └── site_base.css
│   │   │   ├── img
│   │   │   │   └── README
│   │   │   ├── js
│   │   │   │   └── README
│   │   │   └── README
│   │   ├── templates
│   │   │   ├── site_base.html
│   │   │   ├── site_index.html
│   │   └── wsgi.py
~~~


#### Templates and Static Files

As mentioned above, GeoSites uses a hierachy for static files and templates. The first template file found will be the one used so templates in the SITE_ROOT/templates directory will override those in PROJECT_ROOT/templates, which will override those in GEONODE_ROOT/templates.  Static files use a hierarchy similar to the the template directories.  However, they work differently because (on a production server) they are collected and stored in a single location.  Because of this care must be taken to avoid clobbering of files between sites, so each site directory should contain all static files in a subdirectory with the name of the site (e.g., static/siteA/logo.png )

The location of the proper static directory can then be found in the templates syntax such as:

    {{ STATIC_URL }}{{ SITENAME|lower }}/logo.png


#### Permissions by Site

Users are added by default to the site on where they are created and they belong to that site only. However, an admin can add or remvoe people from sites through the "Site People" admin panel (Admin->GeoSites->sitepeople). Select the desired site and move people between the boxes to enable or disable them from the site. 

By default data added to GeoNode is publicly available. In the case of GeoSites, new data will be publicly available, but only for the site it was added to, and the master site (all data is added to the master site). Sharing a resource with other sites involved altering the SiteResource table in the admin panel (Admin->GeoSites->SiteResource).  Add available data to a site or remove by moving resources between the two panels.  Once the changes are saved the sites will have the new resources added (or removed).








