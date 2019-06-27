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

| In GeoNode is possible to create new groups with set of permissions which will be inherited by all the group members.
| The creation of a Group can be done both on the GeoNode UI and on the *Admin Panel*, we will explain how in this paragraph.

The :guilabel:`Create Groups` link of *About* menu in the navigation bar allows administrators to reach the *Group Creation Page*.

.. figure:: img/create_group_page_link.png
    :align: center

    *The Create Group Link*

The following form will open.

.. figure:: img/group_creation_form.png
    :align: center

    *The Group Creation Form*

Fill out all the required fields and click :guilabel:`Create` to create the group.
The *Group Details Page* will open.

.. figure:: img/group_details_page.png
    :align: center

    *The Group Details Page*

The new created group will be searchable in the *Groups List Page*.

.. figure:: img/groups_list_page.png
    :align: center

    *The Groups List Page*

.. note:: The :guilabel:`Create a New Group` button on the *Groups List Page* allows to reach the *Group Creation Form*.

| As already mentioned above, groups can also be created from the Django-based *Admin Interface* of GeoNode.
| The *Groups* link of the *AUTHENTICATION AND AUTHORIZATION* section allows to manage basic Django groups which only care about permissions.
| To create a GeoNode group you should take a look at the *GROUPS* section.

.. figure:: img/groups_admin_section.png
    :align: center

    *The Groups Section on the Admin Panel*

As you can see, GeoNode provides two types of groups. You will learn more about that in the next paragraph.

Types of Groups
^^^^^^^^^^^^^^^

In GeoNode users can be grouped through a *Group Profile*, an enhanced Django group which can be enriched with some further information such as a description, a logo, an email address, some keywords, etc.
It also possible to define some *Group Categories* based on which those group profiles can be divided and filtered.

A new **Group Profile** can be created as follow:

* click on the *Group Profile* :guilabel:`+ Add` button

* fill out all the required fields (see the picture below), *Group Profiles* can be explicitly related to group categories

  .. figure:: img/new_group_profile_form.png
      :align: center

      *A new Group Profile*

* click on :guilabel:`SAVE` to perform the creation, the new created group profile will be visible in the *Group Profiles List*

  .. figure:: img/group_profiles_list.png
      :align: center

      *The Group Profiles List*

Group Categories
^^^^^^^^^^^^^^^^

*Group Profiles* can also be related to *Group Categories* which represents common topics between groups.
In order to add a new **Group Category** follow these steps:

* click on the *Group Categories* :guilabel:`+ Add` button

* fill out the creation form (type *name* and *description*)

  .. figure:: img/new_group_category_form.png
      :align: center

      *A new Group Category*

* click on :guilabel:`SAVE` to perform the creation, the new created category will be visible in the *Group Categories List*

  .. figure:: img/group_categories_list.png
      :align: center

      *The Group Categories List*

| When a GeoNode resource (layer, document or maps) is associated to some *Group Profile*, it is also possible to retrieve the *Group Category* it belongs to.
| So when searching for resources (see :ref:`finding-data`) you can also filter the data by group category.

.. figure:: img/layers_group_category.png
    :align: center

    *Filtering Layers by Group Category*

Managing a Group
================

Through the :guilabel:`Groups` link of *About* menu in the navigation bar, administrators can reach the *Groups List Page*.

.. figure:: img/groups_link.png
    :align: center

    *The Groups Link in the navigation bar*

In that page all the GeoNode *Group Profiles* are listed.

.. figure:: img/group_profiles_list_page.png
    :align: center

    *Group Profiles List Page*

For each group some summary information (such as the *title*, the *description*, the number of *members* and *managers*) are displayed near the *Group Logo*.

Administrators can manage a group from the *Group Profile Details Page* which is reachable by clicking on the *title* of the group.

.. figure:: img/group_profile_details_page.png
    :align: center

    *Group Profile Details Page*

As shown in the picture above, all information about the group are available on that page:

* the group *Title*;
* the *Last Editing Date* which shows a timestamp corresponding to the last editing of the group properties;
* the *Keywords* associated with the group;
* *Permissions* on the group (Public, Public(invite-only), Private);
* *Members* who join the group;
* *Managers* who manage the group.

There are also four links:

* The :guilabel:`Edit Group Details` link opens the *Group Profile Form* through which the following properties can be changed:

  * *Title*.
  * *Logo* (see next paragraphs).
  * *Description*.
  * *Email*, to contact one or all group members.
  * *Keywords*, a comma-separated list of keywords.
  * *Access*, which regulates permissions:

    * *Public*: any registered user can view and join a public group.
    * *Public (invite-only)*: only invited users can join, any registered user can view the group.
    * *Private*: only invited users can join the group, registered users cannot see any details about the group, including membership.

  * *Categories*, the group categories the group belongs to.

  .. figure:: img/group_profile_details_page.png
      :align: center

      *Group Profile Details Page*

* :guilabel:`Managing Group Members` (see next paragraphs).
* the :guilabel:`Delete this Group`, click on it to delete the Group Profile. GeoNode requires you to confirm this action.

  .. figure:: img/confirm_group_deletion.png
      :align: center
      :width: 400px

      *Confirm Group Deletion*

* the :guilabel:`Group Activities` drives you to the *Group Activites Page* where you can see all layers, maps and documents associated with the group. There is also a *Comments* tab which shows comments on those resources.

  .. figure:: img/group_activities.png
      :align: center

      *Group Activities*

Group Logo
^^^^^^^^^^

Each group represents something in common between its members.
So each group should have a *Logo* which graphically represents the idea that identify the group.

On the *Group Profile Form* page you can insert a logo from your disk by click on :guilabel:`Browse...`.

.. figure:: img/editing_group_logo.png
    :align: center

    *Editing the Group Logo*

| Click on :guilabel:`Update` to apply the changes.
| Take a look at your group now, you should be able to see that logo.

.. figure:: img/group_logo.png
    :align: center

    *The Group Logo*

Managing Group members
^^^^^^^^^^^^^^^^^^^^^^

The :guilabel:`Manage Group Members` link opens the *Group Members Page* which shows *Group Members* and *Group Managers*.
**Managers** can edit group details, can delete the group, can see the group activities and can manage memberships.
Other **Members** can only see the group activities.

| In Public Groups, users can join the group without any approval.
  Other types of groups require the user to be invited by the group managers.
| Only group managers can *Add new members*.
  In the picture below, you can see the manager can search for users by typing their names into the *User Identifiers* search bar.
  Once found, he can add them to the group by clicking the :guilabel:`Add Group Members` button.
  The *Assign manager role* flag implies that all the users found will become managers of the group.

.. figure:: img/add_new_member.png
    :align: center

    *Adding a new Member to the Group*

The following picture shows you the results.

.. figure:: img/new_members.png
    :align: center

    *New Members of the Group*

Group based advanced data workflow
==================================

By default GeoNode is configured to make every resource (Layer, Document or Map) suddenly available to everyone, i.e. publicly accessible
even from anonymous/non-logged in users.

It is actually possible to change few configuration settings in order to allow GeoNode to enable an advanced publication workflow.

With the advanced workflow enabled,  your layer, document or map won't be automatically published (i.e. made visible and accessible for all, contributors or simple users).

For now, your item is only visible by yourself, the manager of the group to which the layer, document or map is linked (this information is filled in the metadata), the members of this group, and the GeoNode Administrators.

Before being published, the layer, document or map will follow a two-stage review process, which is described below:

.. figure:: img/adv_data_workflow/adv_data_workflow_001.jpg
    :align: center

    *From upload to publication: the review process on GeoNode*

How to enable the advanced workflow
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You have to tweak the GeoNode settings accordingly.

Please see the details of the following GeoNode ``Settings``:

* `ADMIN_MODERATE_UPLOADS <../../basic/settings/index.html#admin-moderate-uploads>`_

* `GROUP_PRIVATE_RESOURCES <../../basic/settings/index.html#group-private-resources>`_

* `RESOURCE_PUBLISHING <../../basic/settings/index.html#resource-publishing>`_

The group Manager approval
^^^^^^^^^^^^^^^^^^^^^^^^^^
Here, the role of the Manager of the group to which your layer, document or map is linked is to check that the uploaded item is correct.
Particularly, in the case of a layer or a map, it consists of checking that the chosen cartographic representation and the style are
fitting but also that the discretization is appropriate.

The Manager must also check that the metadata are properly completed and that the mandatory information
(Title, Abstract, Edition, Keywords, Category, Group, Region) are filled.

If needed, the Manager can contact the contributor responsible of the layer, document or map in order to report potential comments or
request clarifications.

Members of the group can also take part in the reviewing process and give some potential inputs to the responsible of the
layer, document or map.

When the Manager considers that the layer, document or map is ready to be published, he should approve it.
To do so, the Manager goes to the layer, document or map page, then opens the :guilabel:`Wizard` in order to edit the metadata.
In the :guilabel:`Settings` tab, the manager checks the :guilabel:`Approved` box, and then updates the metadata and saves the changes:

.. figure:: img/adv_data_workflow/approbation_manager.gif
    :align: center

    *The approbation process of an item by a Manager*

Following this approval, the GeoNode Administrators receive a notification informing them that an item is now waiting for publication

.. figure:: img/adv_data_workflow/unpublished.png
    :align: center

    *An approved layer, waiting for publication by the GeoNode administrators*

The publication by the GeoNode Administrator
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Prior to the public release of an approved layer, a document or a map, the Administrator of the platform performs a final validation of
the item and its metadata, notably to check that it is in line with licence policies.

If needed, the GeoNode Administrator can contact the Manager who has approved the layer, document or map, as well as its responsible.

Once the layer, document or map is validated, the item is made public by the Administrator.
It can now be viewed, accessed, and downloaded in accordance with the ``Permissions`` set by the responsible contributor.

Manage profiles using the admin panel
=====================================

So far GeoNode implements two distinct roles, that can be assigned to resources such as layers, maps or documents:

* party who authored the resource
* party who can be contacted for acquiring knowledge about or acquisition of the resource

These two profiles can be set in the GeoNode interface by accessing the metadata page and setting the ``Point of Contact`` and ``Metadata Author`` fields respectively.

Is possible for an administrator to add new roles if needed, by clicking on the :guilabel:`Add Role` button in the :guilabel:`Base -> Contact Roles` section:

.. figure:: img/admin-roles-add.png

Clicking on the :guilabel:`People` section (see figure) will open a web for with some personal information plus a section called :guilabel:`Users`.

.. figure:: img/admin-people.png

Is important that this last section is not modified here unless the administrator is very confident in that operation.

.. figure:: img/admin-profiles-contactroles.png

Manage layers using the admin panel
===================================

Some of the Layers information can be edited directly through the admin interface although the best place is in the :guilabel:`Layer -> Metadata Edit` in GeoNode.

Clicking on the :guilabel:`Admin > Layers` link will show the list of available layers.

.. figure:: img/admin-layers.png

.. warning:: It is not recommended to modify the Layers' ``Attributes`` or ``Styles`` directly from the Admin dashboard unless you are aware of your actions.

The ``Metadata`` information can be changed for multiple Layers at once throguh the :guilabel:`Metadata batch edit` action.

.. figure:: img/admin-layers-batch.png

By clicking over one Layer link, it will show a detail page allowing you to modify some of the resource info like the metadata, the keywords, the title, etc.

.. note:: It is strongly recommended to always use the GeoNode :guilabel:`Metadata Wizard` or :guilabel:`Metadata Advanced` tools in order to edit the metadata info.

Manage the maps using the admin panel
=====================================

Similarly to the Layers, it is possible to manage the available GeoNode Maps through the Admin panel also.

Move to :guilabel:`Admin > Maps` to access the Maps list.

.. figure:: img/admin-maps.png

The ``Metadata`` information can be changed for multiple Maps at once throguh the :guilabel:`Metadata batch edit` action.

.. figure:: img/admin-layers-batch.png

By clicking over one Map link, it will show a detail page allowing you to modify some of the resource info like the metadata, the keywords, the title, etc.

.. note:: It is strongly recommended to always use the GeoNode :guilabel:`Metadata Wizard` or :guilabel:`Metadata Advanced` tools in order to edit the metadata info.

Notice that by enabling the ``Featured`` option here, will allow GeoNode to show the Map thumbnail and the Map detail link on the :guilabel:`Home Page`

.. figure:: img/admin-maps-featured-001.png

.. figure:: img/admin-maps-featured-002.png


Manage the documents using the admin panel
==========================================

Similarly to the Layers and Maps, it is possible to manage the available GeoNode Documents through the Admin panel also.

Move to :guilabel:`Admin > Documents` to access the Documents list.

.. figure:: img/admin-documents.png

The ``Metadata`` information can be changed for multiple Documents at once throguh the :guilabel:`Metadata batch edit` action.

.. figure:: img/admin-layers-batch.png

By clicking over one Document link, it will show a detail page allowing you to modify some of the resource info like the metadata, the keywords, the title, etc.

.. note:: It is strongly recommended to always use the GeoNode :guilabel:`Metadata Wizard` or :guilabel:`Metadata Advanced` tools in order to edit the metadata info.

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
