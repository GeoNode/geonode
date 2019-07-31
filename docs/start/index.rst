.. _geonode_basics:

GeoNode Basics
==============

  .. figure:: img/geonode.png
        :align: center

is a platform for the management and publication of geospatial data.
It brings together mature open-source software projects under an easy to use interface. 

  .. figure:: img/gn_simplified_architecture.png
        :align: center

        *GeoNode simplified architecture*

*With GeoNode, non-specialized users can share data and create interactive maps.*
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  .. figure:: img/gn_is_made_for.png
        :align: center
  .. figure:: img/gn_publication_data.png
        :align: center
  .. figure:: img/gn_publication_data_2.png
        :align: center

Geospatial data storage
^^^^^^^^^^^^^^^^^^^^^^^

GeoNode allows users to upload vector data (currently shapefiles, json, csv, kml and kmz) and raster data in their original projections 
using a web form.

Vector data is converted into geospatial tables on a DB, satellite imagery and other kinds of raster data are retained as GeoTIFFs.

Special importance is given to standard metadata formats like ISO 19139:2007 / ISO 19115 metadata standards.

As soon as the upload is finished, the user can fill the resource metadata in order to make it suddenly available through the `CSW`_ (OGC Catalogue Service)
endpoints and APIs. 

Users may also upload a metadata XML document (ISO, FGDC, and Dublin Core format) to fill key GeoNode metadata elements automatically.

Similarly, GeoNode provides a web based styler that lets the users to change the data portrayals and preview the changes at real time.

.. _CSW: http://www.opengeospatial.org/standards/cat


Data mixing, maps creation
^^^^^^^^^^^^^^^^^^^^^^^^^^

Once the data has been uploaded, GeoNode lets the user search for it geographically or via keywords in order to create fancy maps.

All the layers are automatically re-projected to web Mercator for maps display, making it possible to use different popular base layers, 
like Open Street Map, Google Satellite or Bing layers.

Once the maps are saved, it is possible to embed them in any web page or get a PDF version for printing.

GeoNode as a building block
^^^^^^^^^^^^^^^^^^^^^^^^^^^

A handful of other Open Source projects extend GeoNode's functionality by tapping into the re-usability of Django applications. 

Visit our gallery to see how the community uses GeoNode: `GeoNode Projects <http://geonode.org/gallery/>`_.

The development community is very supportive of new projects and contributes ideas and guidance for newcomers.

Convinced! Where do I sign?
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The next steps are:

1. Make a ride on the :ref:`online_demo`

2. Follow the :ref:`quick_setup_guide` in order to play with your own local instance and access all the admin functionalities

3. Read the documentation starting from the :doc:`user guide </usage/index>` to the :doc:`admin guide </admin/index>`

4. Subscribe to the `geonode-users`_ and/or `geonode-devel`_ mailing lists to join the community.
   See also the section :ref:`get_in_touch` for more info.

Thanks for your interest!

.. _geonode-users: https://lists.osgeo.org/mailman/listinfo/geonode-users
.. _geonode-devel: https://lists.osgeo.org/mailman/listinfo/geonode-devel

.. _supported_browsers:

Supported Browsers
==================

GeoNode is known to be working on all modern web browsers.

This list includes (but is not limited to):

- `Google Chrome <http://www.google.com/chrome/>`_.
- `Apple Safari <https://www.apple.com/safari/>`_.
- `Mozilla Firefox <https://www.mozilla.org/en-US/firefox/new/>`_.
- `Microsoft Edge <https://developer.microsoft.com/en-us/microsoft-edge/>`_.
- Microsoft Internet Explorer.

.. note:: The vast majority of GeoNode developers prefer using Google Chrome.

Internet Explorer
^^^^^^^^^^^^^^^^^

Versions of Microsoft Internet Explorer older than 10, exhibit known issues when used to browse a GeoNode site.
As such a message is displayed warning the user that they should upgrade their browser.

  .. figure:: img/ie_message.png
        :align: center

        *Internet Explorer error message*

Testing on Internet Explorer
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When working on front end code, developers should take care to test carefully with Microsoft Internet Explorer to ensure that the features 
they are working on do indeed work correctly and on this browser. 
It is good practice to test on all browsers available, but the use of modern front end libraries like bootstrap and jQuery make it much 
more likely code will work across browsers seamlessly.

In order to test on Internet Explorer, developers can use the `Modern IE <https://www.modern.ie/en-us>`_ site to download virtual machines 
for use in `Oracle VM Virtual Box <https://www.virtualbox.org/>`_. 

  .. figure:: img/modern_ie.png
        :align: center

        *Testing on Internet Explorer*

Once the VM is downloaded, follow the instructions to configure it in your VirtualBox setup.

    .. figure:: img/virtualbox.png
        :align: center

        *Oracle VirtualBox admin interface*

After the VM is setup, you can access your development instance of GeoNode by visiting the IP address of your host machine or on the bridged interface (usually 10.0.2.2) and begin your testing. 

.. _online_demo:

Online Demo
===========

.. note:: **Disclaimer** we do not guarantee for any data published on this Demo Site. Publish the data at your own risk.
    Every dataset will be removed automatically every Sunday. If you find some dataset that shouldn't be there, please
    write suddenly to developers and maintainers.
    
    See the section :ref:`get_in_touch` for details.

A live demo of the latest stable build is available at http://master.demo.geonode.org/.

  .. figure:: img/online_demo-001.png
        :align: center

        *Online Demo @ master.demo.geonode.org*

Anyone may sign up for a user account, upload and style data, create and share maps, and change permissions.

Since it is a demo site, every sunday all the datasets will be wiped out. Users, passwords and groups will be preserved.

It should hopefully allow you to easily and quickly make a tour of the main capabilities of GeoNode.

.. warning:: This GeoNode instance is configured with standards settings and a very low security level.
    This is a demo only not to be considered a really production ready system.
    For a complete list of settings, refer to the section: :ref:`settings`

.. _quick_setup_guide:

Quick Installation Guide
========================

.. toctree::
    :maxdepth: 3

    quick/index
