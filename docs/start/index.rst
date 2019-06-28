GeoNode Basics
==============

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

.. note:: The vast majority of GeoNode developers perfer using Google Chrome.

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
    Every dataset will be removed automatically every Sunday. If you find some dataset that shouldn't be there, plese
    write suddenly to developers and maintainers.
    
    See the section :ref:`get_in_touch` for details.

A live demo of the latest stable build is available at http://master.demo.geonode.org/.

  .. figure:: img/online_demo-001.png
        :align: center

        *Online Demo @ master.demo.geonode.org*

Anyone may sign up for a user account, upload and style data, create and share maps, and change permissions.

Since it is a demo site, every sunday al the datasets will be wiped out. Users, passwords and groups will be preserved.

It should hopefully allow you to easily and quickly make a tour of the main capabilities of GeoNode.

.. warning:: This GeoNode instance is configured with standars settings and a very low security level.
    This is a demo only not to be considered a really production ready system.
    For a complete list of settings, refer to the section: :ref:`settings`

Quick Installation Guide
========================

.. toctree::
    :maxdepth: 3

    quick/index
