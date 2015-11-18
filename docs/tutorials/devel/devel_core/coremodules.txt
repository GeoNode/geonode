.. _coremodules:

GeoNode's Core Modules
======================

GeoNode is made up of a set of core Django pluggable modules (known as apps in Django) that provide the functionality of the application. Together they make up the key components of a GeoNode site. While your own use case and implementation may not require that you work directly on these modles, it is important that you become familiar with their layout, structure and the functionality that they provide. You may need to import these apps into your own apps, and as such, becoming familiar with them is an important step in becoming a proficient GeoNode developer.

geonode.layers
--------------

geonode.layers is the most key GeoNode module. It is used to represent layers of data stored in a GeoNode's paired GeoServer. The layer model class inherits fields from the ResourceBase class which provides all of the fields necessary for the metadata catalogue, and adds fields that map the object to its corresponding layer in GeoServer. When your users upload a layer via the user interface, the layer is imported to GeoServer and a record is added to GeoNode's database to represent that GeoServer layer within GeoNode itself. 

The Layer model class provides a set of helper methods that are used to perform operations on a Layer object, and also to return things such as the list of Download or Metadata links for that layer. Additional classes are used to model the layers Attributes, Styles, Contacts and Links. The Django signals framework is used to invoke specific functions to synchronize with GeoServer before and after the layer is saved. 

The views in the layers app are used to perform functions such as uploading, replacing, removing or changing the points of contact for a layer, and views are also used to update layer styles, download layers in bulk or change a layers permissions.

The forms module in the layer app is used to drive the user interface forms necessary for performing the business logic that the views provide. 

The Layers app also includes a set of templates that are paired with views and used to drive the user interface. A small set of layer template tags is also used to help drive the layer explore and search pages.

Some helper modules such as geonode.layers.metadata and geonode.layers.ows are used by the layer views to perform specific functions and help keep the main views module more concise and legible. 

Additionally, the GeoNode specific management commands are a part of the geonode.layers app.

You should spend some time to review the layers app through GitHubs code browsing interface.

https://github.com/GeoNode/geonode/tree/master/geonode/layers

geonode.maps
------------

The geonode.maps app is used to group together GeoNodes multi layer map functionality. The Map and MapLayer objects are used to model and implement maps created with the GeoExplorer application. The Map object also extends from the ResourceBase class which provides the ability to manage a full set of metadata fields for a Map.

The views in the maps app perform many of the same functions as the views in the layers app such as adding, changing, replacing or removing a map and also provide the endpoints for returning the map configuration from the database that is used to initialize the GeoExplorer app. 

The maps app also includes a set of forms, customization of the Django admin, some utility functions and a set of templates and template tags.

You can familiarize yourself with the maps app on GitHub.

https://github.com/GeoNode/geonode/tree/master/geonode/layers

geonode.security
----------------

The geonode.security app is used to provide object level permissions within the GeoNode Django application. It is a custom Django authentication backend and is used to assign Generic, User and Group Permissions to Layers, Maps and other objects in the GeoNode system. Generic permissions are used to enable public anonymous or authenticated viewing and/or editing of your data layers and maps, and User and Group specific permissions are used to allow specific users or groups to access and edit your layers. 

geonode.search
--------------

The geonode.search module provides the search API that is used to drive the GeoNode search pages. It is configured to index layers, maps, documents and profiles, but is extensible to allow you to use it to index your own model classes. This module is currently based on the Django ORM and as such has a limited set of search features, but the GeoNode development team is actively working on making it possible to use this module with more feature-rich search engines.

geonode.catalogue
-----------------

The geonode.catalogue app provides a key set of metadata catalogue functions within GeoNode itself. GeoNode is configured to use an integrated version of the pycsw library to perform these functions, but can also be configured to use any OGC compliant CS-W implementation such as GeoNetwork or Deegree. The metadata app allows users to import and/or edit metadata for their layers, maps and documents, and it provides an OGC compliant search interface for use in federating with other systems.

geonode.geoserver
-----------------

The geonode.geoserver module is used to interact with GeoServer from within GeoNode's python code. It relies heavily on the gsconfig library which addresses GeoServer's REST configuration API. Additionally, the geonode.geoserver.uploader module is used to interact with GeoServers Importer API for uploading and configuring layers.

geonode.people
--------------

The geonode.people module is used to model and store information about both GeoNode users and people outside of the system who are listed as Points of Contact for particular layers. It is the foundational module for GeoNode's social features. It provides a set of forms for users to edit and manage their own profiles as well as to view and interact with the profiles of other users.

geoexplorer
-----------

GeoNode's core GIS client functions are performed by GeoExplorer. The GeoExplorer app is in turn based on GeoExt, OpenLayers and ExtJS. It provides functionality for constructing maps, styling layers and connecting to remote services. GeoExplorer is the reference implementation of the OpenGeo Suite SDK which is based on GXP. GeoNode treats GeoExplorer as an external module that is used out of the box in GeoNode, but it is possible for you to create your own Suite SDK app and integrate it with GeoNode.  

Static Site
-----------

The front end of GeoNode is composed of a set of core templates, specific templates for each module, cascading style sheets to style those pages and a set of javascript modules that provide the interactive functionality in the site. 

Templates
~~~~~~~~~

GeoNode includes a basic set of core templates that use Django's template inheritance system to provide a modular system for constructing the web pages in GeoNode's interface. These core templates drive the overall page layout and things like the home page. You will start the process of customizing your GeoNode instance by overriding these templates, so you should familiarize yourself with their 
tructure and how they inherit from each other to drive the pages. 

Additionally, most of the apps described above have their own set of templates that are used to drive the pages for each module. You may also want to override these templates for your own purposes and as such should familiarize yourself with a few of the key ones.

CSS
~~~

GeoNode's css is based on Twitter's Bootstrap Library which uses the lessc dynamic stylesheet language. GeoNode extends from the basic Boostrap style and you are able to create your own bootstrap based style to customize the look and feel of your own GeoNode instance. Sites like bootswatch.com also provide ready made styles that you can simply drop in to your project to change the style.

Javascript
~~~~~~~~~~

The interactive functionality in GeoNode pages is provided by the jQuery javascript framework and a set of jQuery plugins. The core set of GeoNode javascript modules closely aligns with the apps described above, and there are also a few pieces of functionality provided as javascript modules that are used through out all of the apps. You are able to add your own jQuery code and/or plugins to perform interactive functionality in your own application. 
