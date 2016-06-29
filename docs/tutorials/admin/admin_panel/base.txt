.. _admin_panel.base:


Manage the metadata categories using the admin panel
====================================================

In the "Base" section of the admin panel there are the links to manage the metadata categories used in GeoNode

.. figure:: img/admin-base.png

The metadata categories are:

* Regions
* Restriction Code Types
* Spatial Representation Types
* Topic Categories

The other links available should not be used.


Regions
-------

The Regions can be updated, deleted and added on needs. Just after a GeoNode fresh installation the regions contain all of the world countries, identified by their ISO code.

.. figure:: img/admin-base-region-list.png

Restriction Code Types
----------------------

Being GeoNode strictly tied to the standards, the restrictions cannot be added/deleted or modified in their identifier. This behavior is necessary to keep the consistency in case of federation with the CSW catalogues.

The Restrictions GeoNode description field can in any case be modified if some kind of customisation is necessary, since it's just the string that will appear on the layer metadata page. If some of the restrictions are not needed within the GeoNode instance, it is possible to hide them by unchecking the "Is choice" field.

.. figure:: img/admin-base-restriction-list.png

Spatial Representation Types
----------------------------

For this section the same concepts of the Restriction Code Types applies.

.. figure:: img/admin-base-spatialrepresentation-list.png

Topic Categories
----------------

Also for the Topic Categories the only part editable is the GeoNode description.
Being standard is assumed that every possible data type will fall under these category identifiers.
If some of the categories are not needed within the GeoNode instance, it is possible to hide them by unchecking the "Is choice" field.

.. figure:: img/admin-base-topiccategories-list.png

