Accessing the panel
===================

| The *Admin Panel* is a model-centric interface where trusted users can manage content on GeoNode.
| Only the staff users can access the admin interface.

.. note:: The “staff” flag, which controls whether the user is allowed to log in to the admin interface, can be set by the admin panel itself.

The panel can be reached from :guilabel:`Admin` link of the *User Menu* in the navigation bar (see the picture below) or through this URL: ``http://<your_geonode_host>/admin``.

.. figure:: img/admin_link.png
     :align: center

     *The Admin Link of the User Menu*

When clicking on that link the Django-based *Admin Interface* page opens and shows you all the Django models registered in GeoNode.

.. figure:: img/django_geonode_admin_interface.png
     :align: center

     *The GeoNode Admin Interface*

Reset or Change the admin password
==================================

From the *Admin Interface* you can access the :guilabel:`CHANGE PASSWORD` link on the right side of the navigation bar.

.. figure:: img/change_password_link.png
     :align: center

     *The Change Password Link*

It allows you to access the *Change Password Form* through which you can change your password.

.. figure:: img/change_password_form.png
     :align: center

     *The Change Password Form*

Once the fields have been filled out, click on :guilabel:`CHANGE MY PASSWORD` to perform the change.

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

Partners
^^^^^^^^

GeoNode simple theming, allows also a ``Partners`` section, in order to easily list links to third-party institutions collaborating to the project.

The example below shows the ``Partners`` section of `WorldBank CHIANG MAI URBAN FLOODING <https://urbanflooding.geo-solutions.it/>`_ GeoNode instance
made through integrating theming options.

.. figure:: img/theming/theme-def-0005.png
    :align: center

    *Urbanflooding GeoNode Partners Section*

The ``Partners`` items can be managed through the ``http://<your_geonode_host>/admin/geonode_themes/partner/`` Admin section

.. figure:: img/theming/theme-def-0005a.png
    :align: center

    *GeoNode Partners Admin Section*

From here it is possible to add, modify or delete partners items.

A new partner is defined by few elements, a ``Logo``, a ``Name``, a ``Display Name`` and a ``Website``

.. figure:: img/theming/theme-def-0005b.png
    :align: center

    *Add a Partner*

In order to attach or detach a ``Partner`` to an existing ``Theme`` on GeoNode, you will need to edit the Theme and go to the ``Partners`` section

.. figure:: img/theming/theme-def-0005c.png
    :align: center

    *Theme Partners Section*

From here you will be able to either to change the ``Partners title`` text and/or select/deselect ``Partners`` from the ``multi-select`` box.

.. note:: In order to select/deselect elements from the ``multi-select`` box, you **must** use the ``CTRL+CLICK`` button combintation.

Privacy Policies and Cookie settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By enabling the ``Cookies Law Info Bar`` checkbox (``True`` by default)

.. figure:: img/theming/theme-def-0006.png
    :align: center

    *Cookies Law Info Bar checkbox*

it will be possible to allow GeoNode presenting the `Privacy Policies and Cookie settings` pop-ups and links at the bottom of the home page

.. figure:: img/theming/theme-def-0006a.png
    :align: center

    *Cookies Law Info Bar*

There are plenty of options available, allowing you to customize contact info as long as colors of the bar and page.

One of the most importat to consider it is for sure the ``Cookie law info bar text``

.. figure:: img/theming/theme-def-0006b.png
    :align: center

    *Cookie law info bar text*

The default text contained in this section is the following one

.. code-block:: html

    This website uses cookies to improve your experience,
    check <strong><a style="color:#000000" href="/privacy_cookies/">this page</a></strong> for details.
    We'll assume you're ok with this, but you can opt-out if you wish.


The text can be changed and customized, of course. Nevertheless it points by default to the following page

.. code-block:: shell

    /privacy_cookies/

aka `http://<your_geonode_host>/privacy_cookies/`

.. figure:: img/theming/theme-def-0006c.png
    :align: center

    */privacy_cookies/ Default Page*

The page contains a default generic text along with some placeholders, which, most probably, won't feet your needs.

In order to change this you have two options:

1. Change the link reported into the ``Cookie law info bar text`` section, to make it pointing to an external/static page.

2. Change the contents of ``/geonode/templates/privacy-cookies.html`` Django template accordingly to your needs; this is basically a plain ``HTML`` page which can be easily customized by using a standard text editor.

Switching between different themes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In the case you have defined more Themes, switching between them is as easy as ``enabling`` one and ``disabling`` the others.

Remember to save the Themes everytime and refresh the GeoNode home page on the browser to see the changes.

It is also important that there is **only one** Theme enabled **at a time**.

In order to go back to the standard GeoNode behavior, just disable or delete all the available Themes.

Invite a User
=============

Add a new user
==============

In GeoNode, administrators can manage other users. For example, they can *Add New Users* through the following form.

.. figure:: img/add_user_form.png
    :align: center

    *Adding New Users*

The form above can be reached from the *Admin Panel* at the following path: *Home > People > Users*. Click on :guilabel:`ADD USER +` to open the form page.

.. figure:: img/add_user_button.png
    :align: center

    *The Add User button in the Users List page*

It is also available, in the GeoNode UI, the :guilabel:`Add User` link of the *About* menu in the navigation bar.

.. figure:: img/add_user_link.png
    :align: center

    *Add User Link*

To perform the user creation fill out the required fields (*username* and *password*) and click on :guilabel:`SAVE`.
You will be redirected to the *User Details Page* which allows to insert further information about the user.

.. figure:: img/user_details_admin_page.png
    :align: center

    *The User Details Page*

The user will be visible into the *Users List Page* of the *Admin Panel* and in the *People Page* (see :ref:`user-info`).

.. figure:: img/new_user_in_people.png
    :align: center

    *The User in the People page*

Activate/Disable a User
=======================

When created, new users are *active* by default.
You can check that in the *User Details Page* from the *Admin Panel* (see the picture below).

.. figure:: img/new_user_active.png
    :align: center

    *New Users Active by default*

| *Active* users can interact with other users and groups, can manage resources and, more in general, can take actions on the GeoNode platform.
| Untick the *Active* checkbox to disable the user. It will be not considered as user by the GeoNode system.

.. figure:: img/new_user_disabled.png
    :align: center

    *Disabeld Users*

Change a User password
======================

GeoNode administrators can also change/reset the password for those users who forget it.
As shown in the picture below, click on ``this form`` link from the *User Details Page* to access the *Change Password Form*.

.. figure:: img/change_user_password_link.png
    :align: center

    *Changing Users Passwords*

The *Change User Password Form* should looks like the following one.
Insert the new password two times and click on :guilabel:`CHANGE PASSWORD`.

.. figure:: img/chenge_user_password_form.png
    :align: center

    *Changing Users Passwords*

Promoting a User to Staff member or superuser
=============================================

Active users have not access to admin tools.
GeoNode makes available those tools only to *Staff Members* who have the needed permissions.
*Superusers* are staff members with full access to admin tools (all permissions are assigned to them).

Administrators can promote a user to *Staff Member* by ticking the **Staff status** checkbox in the *User Details Page*.
To make some user a *Superuser*, the **Superuser status** checkbox should be ticked. See the picture below.

.. figure:: img/staff_and_superuser_permissions.png
    :align: center

    *Staff and Superuser permissions*

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
