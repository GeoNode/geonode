.. _admin_panel:

==================================================
Usage of the GeoNode's Django Administration Panel
==================================================

GeoNode has an administration panel based on the Django admin which 
can be used to do some database operations.
Although most of the operations can and should be done through the normal GeoNode interface, the admin panel provides a quick overview and management tool over the
database.

It should be highlighted that the sections not covered in this guide are meant to be managed through GeoNode.

Accessing the admin panel
=========================

Only the staff users (including the superusers) can access the admin interface.

.. note:: User's staff membership can be set by the admin panel itself, see how in the :ref:`admin_panel.users-groups` section.

The link to access the admin interface can be found by clicking in the upper right corner on the user name, see figure

.. figure:: img/admin-login.png


.. toctree::
   :maxdepth: 1

   users-groups
   profiles
   base
   layers
   maps
   documents
