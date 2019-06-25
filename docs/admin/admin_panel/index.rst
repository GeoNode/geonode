Accessing the panel
===================

Reset or Change the admin password
==================================

Simple Theming
==============

GeoNode provides by default some theming options manageable directly from the Administration panel. 
Most of the times those options allows you to easily change the GeoNode look and feel without touching a single line of `HTML` or `CSS`.

As an `administrator` go to ``http://<your_geonode_host>/admin/geonode_themes/geonodethemecustomization/``.

.. figure:: img/theming/themes.png
    :align: center

    *List of available Themes*

The panel shows all the available GeoNode themes, if any, and allows you to create new ones.

.. warning:: Only one theme at a time can be **activated** (aka *enabled*). By disabling or deleting all the available themes, GeoNode will turn the gui back to the default one.

Editing or creating a new Theme, will actually allow you to customize several properties.

At least you'll need to provide a ``Name`` for the Theme. Optionally you can specify also a ``Description``, which will allow you to better
identify the type of Theme you created.

.. figure:: img/theming/theme-def-0001.png
    :align: center

    *Theme Name and Description*

Just below the ``Description`` field, you will find the ``Enabled`` checkbox, allowing you to toggle the Theme.

.. figure:: img/theming/theme-def-0002.png
    :align: center

    *Theme Name and Description*

Jumbotron and Get Started link
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. note:: Remember, everytime you want to apply some changes to the Theme, you **must** save the Theme and reload the GeoNode browser tab.
    In order to quickly switch back to the Home page, you can just click the ``VIEW SITE`` link on the top-right corner of the Admin dashboard.

    .. figure:: img/theming/theme-def-0003c.png
        :align: center

The next section, allows you to define the first important Theme properties. This part involves the GeoNode main page sections.

.. figure:: img/theming/theme-def-0003.png
    :align: center

    *Jumbotron and Logo options*

By changing those properties as shown above, you will easily change your default home page from this

.. figure:: img/theming/theme-def-0003a.png
    :align: center

    *GeoNode Default Home*

to this

.. figure:: img/theming/theme-def-0003b.png
    :align: center

    *Updating Jumbotron and Logo*

It is possible to optionally **hide** the ``Jumbotron text`` and/or the ``Call to action`` button

.. figure:: img/theming/theme-def-0003d.png
    :align: center

.. figure:: img/theming/theme-def-0003e.png
    :align: center

    *Hide Jumbotron text and Call to action button*

Copyright and contact info footer
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The default GeoNode footer does not present any type of contact info.

.. figure:: img/theming/theme-def-0004.png
    :align: center

    *Default GeoNode Footer*

By enabling and editing the ``contact us box`` fields

.. figure:: img/theming/theme-def-0004a.png
    :align: center

    *Enable contact us box*

it will be possible to show a simple *Contact Us* info box on the GeoNode footer section.

.. figure:: img/theming/theme-def-0004b.png
    :align: center

    *Contact Us Footer*

Similarly, by editing the ``Copyright`` text box and/or background color

.. figure:: img/theming/theme-def-0004c.png
    :align: center

    *Copyright Text and Color*

it will be possible to show the Copyright statement to the bottom of the page

.. figure:: img/theming/theme-def-0004d.png
    :align: center

    *Copyright*

Invite a User
=============

Add a new user
==============

Activate/Disable a User
=======================

Change a User password
======================

Promoting a User to Staff member or superuser
=============================================

Creating a Group
================

Managing a Group
================

Group based advanced data workflow
==================================

Manage profiles using the admin panel
=====================================

Manage layers using the admin panel
===================================

Manage the maps using the admin panel
=====================================

Manage the documents using the admin panel
==========================================

Announcements
=============

Keywords
========

Licenses
========

Topic Categories
================

Regions
=======

Menus, Items and Placeholders
=============================

OAuth2 Access Tokens
====================