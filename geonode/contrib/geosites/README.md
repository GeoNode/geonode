===============================
GeoSites: GeoNode Multi-Tenancy
===============================

GeoSites is a contrib module to GeoNode starting with 2.4. The GeoSites app is a way to run multiple websites with a single instance of GeoNode. Each GeoSite can have different templates, applications, and data permissions but share a single database, web mapping service (GeoServer), and CSW (PyCSW).  This is useful when multiple websites are desired to support different sets of users, but with a similar set of data and overall look and feel of the sites.  Users can be given permission to access multiple sites if needed, which also allows administrative groups can be set up to support all sites with one account.

A GeoSites installation uses a 'master' GeoNode website that has access to all users, groups, and data. Through the Django admin page, Layers, Maps, Documents, Users, and Groups can be added and removed from all sites.  Users can be given access to any number of sites, and data may appear on only a single site, or all of them.  The master site need not be accessible from the outside so that it can be used as an internal tool to the organization.


GeoSites Project
============================
A GeoSites project looks similar to a normal GeoNode project, but with additional folders for sites, and more settings files. In the project there is a directory for each site: 'master' and 'site2' in the example listing below. Each site folder contains a settings file (and optionally local_settings) with site specific settings, as well as directories for static files and Django templates. In addition are configuration files necessary to serve the site: nginx, gunicorn, and wsgi.py.

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

Master Website
============================
Users created on a site are created with access to just that site (but not the master site).  Data uploaded to a site is given permission on that site as well as the master site.


Settings
============================
Site settings are managed through the use of common settings files as well as site specific settings files.   A simple site settings file looks like this:

~~~
###############################################
# Geosite settings
###############################################

import os
from geonode.contrib import geosites

# Directory of master site
GEOSITES_ROOT = os.path.dirname(geosites.__file__)
SITE_ROOT = os.path.dirname(__file__)

# Read in GeoSites pre_settings
execfile(os.path.join(GEOSITES_ROOT, 'pre_settings.py'))

SITE_ID = $SITE_ID  # flake8: noqa
SITE_NAME = '$SITE_NAME'
# Should be unique for each site
SECRET_KEY = "fbk3CC3N6jt1AU9mGIcI"

# site installed apps
SITE_APPS = ()

# Site specific databases
SITE_DATABASES = {}

# Overrides

# Below are some common GeoNode settings that might be overridden for site

# base urls for all sites
# ROOT_URLCONF = 'geosites.urls'

# admin email
# THEME_ACCOUNT_CONTACT_EMAIL = ''

# Have GeoServer use this database for this site
# DATASTORE = ''

# Allow users to register
# REGISTRATION_OPEN = True

# These are some production settings that should be changed here or in local_settings
# SITEURL = 'http://example.com'
# OGC_SERVER['default']['LOCATION'] = os.path.join(GEOSERVER_URL, 'geoserver/')
# OGC_SERVER['default']['PUBLIC_LOCATION'] = os.path.join(SITEURL, 'geoserver/')


# Read in GeoSites post_settings
execfile(os.path.join(GEOSITES_ROOT, 'post_settings.py'))
~~~




A key component in managing multiple sites is keeping data organized and using a structured series of settings files so that common settings can be shared and only site specific settings are separated out. It is also best to import the default GeoNode settings from the GeoNode installation.  This prevents the settings from having to be manually upgraded if there is any default change the GeoNode settings.

While Django apps on other sites are not automatically added, for single site administration they can be added to the master site through the master site settings.py file. 



Database
=====================
The master site, and all of the individual GeoSites, share a single database. Objects, including users, groups, and data layers, all appear within the database but an additional sites table indicates which objects have access to which sites.  The geospatial data served by GeoServer (e.g., from PostGIS) can exist in the database like normal, since GeoServer will authenticate against GeoNode, which will use it's database to determine permissions based on the object, current user, and site.

By default data added to GeoNode is publicly available. In the case of GeoSites, new data will be publicly available, but only for the site it was added to, and the master site (all data is added to the master site). 


GeoServer
=====================
A single GeoServer instance is used to serve data to all of the GeoSites.  To keep data organized each site specifies a default workspace (DEFAULT_WORKSPACE) that GeoServer will use to partition the data depending on which site uploaded the data.   The workspaces themselves don't have any impact on permissions, since data can be added and removed from different sites, however it provides at least some organization of the data based on the initial site.

Data that is common to all sites can be added to the master site which will appear in the generic 'geonode' workspace.


Settings Files and Templates
=============================



Settings which are common to all GeoSites, but differ from the default GeoNode, are separated into a master_settings.py file.  Then, each individual site has settings file which imports from the master site and will then only need to specify a small selection that make that site unique, such as:

* SITE_ID: Each one is unique, the master site should have a SITE_ID of 1.
* SITENAME
* SITEURL
* ROOT_URLCONF: This may be optional. The master site url.conf can be configured to automatically import the urls.py of all SITE_APPS, so a different ROOT_URLCONF is only needed if there are further differences.
* SITE_APPS: Containing the site specific apps
* App settings: Any further settings required for the above sites
* Other site specific settings, such as REGISTRATION_OPEN

A GeoSite therefore has three layers of imports, which is used for settings as well as the search path for templates. First it uses the individual site files, then the master GeoSite, then default GeoNode. These are specified via variables defined in settings:

* SITE_ROOT: The directory where the site specific settings and files are located (templates, static)
* PROJECT_ROOT: The top-level directory of all the GeoSites which should include the global settings file as well as template and static files
* GEONODE_ROOT: The GeoNode directory.

The TEMPLATE_DIRS, and STATICFILES_DIRS will then include all three directories as shown::

    TEMPLATE_DIRS = (
        os.path.join(SITE_ROOT, 'templates/'),
        os.path.join(PROJECT_ROOT,'templates/'),  # files common to all sites
        os.path.join(GEONODE_ROOT, 'templates/')
    )

    STATICFILES_DIRS = (
        os.path.join(SITE_ROOT, 'static/'),
        os.path.join(PROJECT_ROOT, 'static/'),
        os.path.join(GEONODE_ROOT, 'static/')
    )

At the end of the settings_global.py the following variables will be set based on site specific settings::

    STATIC_URL = os.path.join(SITEURL,’static/’)
    GEONODE_CLIENT_LOCATION = os.path.join(STATIC_URL,’geonode/’)
    GEOSERVER_BASE_URL = SITEURL + ‘geoserver/’
    if SITE_APPS:
        INSTALLED_APPS += SITE_APPS

Templates 
==========================




Static Files
==========================

As mentioned above for each website there will be three directories used for template and static files.  The first template file found will be the one used so templates in the SITE_ROOT/templates directory will override those in PROJECT_ROOT/templates, which will override those in GEONODE_ROOT/templates.

Static files use a hierarchy similar to the the template directories.  However, they work differently because (on a production server) they are collected and stored in a single location.  Because of this care must be taken to avoid clobbering of files between sites, so each site directory should contain all static files in a subdirectory with the name of the site (e.g., static/siteA/logo.png )

The location of the proper static directory can then be found in the templates syntax such as::

    {{ STATIC_URL }}{{ SITENAME|lower }}/logo.png

Permissions by Site
================


Adding New Sites
===============
A management command exists to easily create a new site.  This will create all the needed directories, as well as a site specific settings file.  The command may also create a website configuration file.

    $ python manage.py addsite sitename sitedomain
    # example
    $ python manage.py addsite site3 site3.example.com


