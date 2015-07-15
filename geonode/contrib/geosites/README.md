===============================
GeoSites: GeoNode Multi-Tenancy
===============================

GeoSites is a way to run multiple websites with a single instance of GeoNode. Each GeoSite can have different templates, apps, and data permissions but share a single database (useful for sharing users and data layers), GeoServer, and CSW.  This is useful when multiple websites are desired to support different sets of users, but with a similar set of data and overall look and feel of the sites.  Users can be given permission to access multiple sites if needed, which also allows administrative groups can be set up to support all sites with one account.


Master Website
============================

A GeoSites installation uses a 'master' GeoNode website that has soms additional administrative pages for doing data management. Layers, Maps, Documents, Users, and Groups can all be added and removed from different sites.  Users can be given access to any number of sites, and data may appear on only a single site, or all of them.  Additionally, if desired, any or all of the django apps installed on the other sites can be added to the master site to provide a single administrative interface that gives full access to all apps.  The master site need not be accessible from the outside so that it can be used as an internal tool to the organization.

Users created on a particular site are created with access to just that site.  Data uploaded to a particular site is given permission on that site as well as the master site.   Any further adjustments to site-based permissions must be done from the master site.

Database
=====================
The master site, and all of the individual GeoSites, share a single database. Objects, including users, groups, and data layers, all appear within the database but an additional sites table indicates which objects have access to which sites.  The geospatial data served by GeoServer (e.g., from PostGIS) can exist in the database like normal, since GeoServer will authenticate against GeoNode, which will use it's database to determine permissions based on the object, current user, and site.


GeoServer
=====================
A single GeoServer instance is used to serve data to all of the GeoSites.  To keep data organized each site specifies a default workspace (DEFAULT_WORKSPACE) that GeoServer will use to partition the data depending on which site uploaded the data.   The workspaces themselves don't have any impact on permissions, since data can be added and removed from different sites, however it provides at least some organization of the data based on the initial site.

Data that is common to all sites can be added to the master site which will appear in the generic 'geonode' workspace.


Settings Files and Templates
=============================

A key component in managing multiple sites is keeping data organized and using a structured series of settings files so that common settings can be shared and only site specific settings are separated out. It is also best to import the default GeoNode settings from the GeoNode installation.  This prevents the settings from having to be manually upgraded if there is any default change the GeoNode settings.

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

Templates and Static Files
==========================

As mentioned above for each website there will be three directories used for template and static files.  The first template file found will be the one used so templates in the SITE_ROOT/templates directory will override those in PROJECT_ROOT/templates, which will override those in GEONODE_ROOT/templates.

Static files work differently because (at least on a production server) they are collected and stored in a single location.  Because of this care must be taken to avoid clobbering of files between sites, so each site directory should contain all static files in a subdirectory with the name of the site (e.g., static/siteA/logo.png )

The location of the proper static directory can then be found in the templates syntax such as::

    {{ STATIC_URL }}{{ SITENAME|lower }}/logo.png

Permissions by Site
================
By default GeoNode is publicly available. In the case of GeoSites, new data will be publicly available, but only for the site it was added to, and the master site (all data is added to the master site). 

Adding New Sites
===============
A management command exists to easily create a new site.  This will create all the needed directories, as well as a site specific settings file.  The command may also create a website configuration file.
