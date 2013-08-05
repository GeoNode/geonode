===================================
Security and Permissions (Tutorial)
===================================

This tutorial will guide you through the steps that can be done in order to restrict the access on your data uploaded to geonode.


First of all it will be shown how a user can be created and what permissions he can have. Secondly we will take a closer look
on to layers, maps and documents and the different opportunities you have in order to ban certain users from viewing or editing your
data.

Users
-----

Your first step will be to create a user. To do so you are having more than only one possibility. Depending on which kind of user you want to create you may
choose a different option. We will start with creating a superuser, because this user will be your *administrator*. A superuser
has all the permissions without explicity assigning them.

The easiest way to create a superuser (in linux) is to open your terminal and type::

  source .venvs/geonode/bin activate
  django-admin.py createsuperuser --settings=geonode.settings
  
This can only be done when you've installed geonode by source. If you did another kind of installation you should be able to
use this command::
  
  geonode createsuperuser
  
Now you've created a superuser you should become familiar with the *Django Admin Interface* As a superuser you are having
access to this interface, where you can manage users, layers, permission and more. To learn more detailed about this interface
check LINK. For now it will be enough to just follow the steps. To attend the *Django Admin Interface*, click onto your name
on the right top of the geonode website (when you've already logged in with your superuser account). Then the following menu
will show up:

  .. figure:: img/menu_admin.PNG

Click on to *Admin* and the interface will show up.

  .. figure:: img/admin_interface.PNG
  
Go to *Auth* -> *Users* and you will see all the users that exist at the moment. In your case it will only be the superuser you've
just created. Click on it, and you will see a section on *Personal Info*, one on *Permissions* and one on *Important dates*. For
us, the section on *Permissions* is the most important.

  .. figure:: img/permissions_django_admin.PNG

As you can see, there are three boxes that can be checked and unchecked. Because you created a superuser, all three boxes
are checked as default. If only the box *active* would have been checked, the user would not be a superuser and would not be able to
attend the *Django Admin Interface* (which is only available for users with the *staff* status). Therefore keep the following
two things in mind:

* a superuser is able to attend the *Django Admin Interface* and he has all permissions on the data uploaded to geonode.
* a normal user (created from geonode interface) does only have to status *active* as default. This user does not have the ability to attend the *Django Admin Interface* and certain permissions have to be added for him.

Until now we've only created a superuser. But how to create a normal user? You could use the *Django Admin Interface* to do so or do it directly on the geonode website. 

#. Django Admin Interface

   Go to *Auth* -> *Users* and you should find a button on the right that says *Add user*. 

   .. figure:: img/add_user.PNG
 
   Click on it and a form to fill out will appear.

   .. figure:: img/add_test_user.PNG
  
   Fill out the form, and then click *save* at the right bottom of the site. Now you should be directed to the site where you can
   change the permissions on the user *test_user*. As default only *active* is checked. If you want this user also to be able to attend the *Django Admin Interface*
   you can also check *staff status*. For now we leave the settings as they are!

   .. todo:: groups and permissions!
   
   Now a new user has been created and could be logged in from the geonode website as well.

#. Geonode website

   To create an ordinary user you could also just use the geonode website. If you installed geonode using a release, you should
   be able to see a *Register* button on the top, beside the *Sign in* button. Hit the button and a form will appear for you to fill out.
  
   .. figure:: img/sign_up_test_user.PNG

   By hitting *Sign up* the user will be signed up, as default only with the status *active*.
   To change or add a status to a certain user you have to attend the *Django Admin Interface* and go to *Auth* -> *Users* again.
   Click on the user you want to change and you will be able to change personal information as well as permissions.
   
   .. note:: If you've installed geonode in developing mode, the *Register* button won't be seen from the beginning. To add this button to the website, you have
   to change the `REGISTRATION_OPEN = False` in the settings.py to `REGISTRATION_OPEN = True`. Then reload geonode and you should also be able to see the *Register* button.
   
You you should know about the different kinds of users and how to create them. You've also learned about the permissions a certain user has and how to change them using the *Django Amdin Interface*.


Layers
------

Now we take a closer look on the security of layers, how you can protect your data not to be viewed or edited by unwanted users.
As already mentioned before it is important to know that a superuser does have unrestricted access to all your uploaeded data.
That means you cannot ban a superuser from viewing or editing a layer.

.. todo:: maybe you could do that, using the django admin interface

The permissions on your layers can already be set when uploading your files. When the upload form appears you will see the permission
section on the right side:

  .. figure:: img/upload_layer.PNG
  
You access on your layer is split up into three groups:

* view and download data
* edit data
* manage and edit data

The difference between *manage and edit layer* and simply *edit layer* is only, that a user assigned to *edit layer* is not able to change
the permissions on the layer (as a user assigned to *manage and edit layer* is!).
You can now coose whether you want your layer to be viewed and downloaded by

* anyone
* any registered user
* a certain user (or group)

If you want your layer only be viewed by certain users or a group, you have to choose *Only users who can edit* in the part *Who can view and download this data*.
In the section *Who can edit this data* you write down the names of the users you want to have admission on this data.0

.. todo:: BUG about view => only users who can edit => not working; have to set it to any registered users!

When adding a layer using *importlayers* or when you upload new layers on geoserver and make them available on geonode using *updatelayers* (see section ...) you can edit the permissions on these layers later on as well. 
If you are the owner of the layers, resp. the one who uploaded them, you can change the permissions of a specific layer by hitting the *Edit Layer* button.

  .. figure:: img/edit_and_download_layer.PNG

  .. figure:: img/edit_and_manage.PNG
  
Choose *edit permissions* and a window with the permission settings will appear. This window can also be opened by scrolling down the website. On the right handside of
the page you should be able to see a button like this.

  .. figure:: img/change_layer_permissions.PNG
  
Click it and you will see the same window.

If you allow a certain user only to view and download data, the button *edit layer* will vanish. But when you assign a user to be able
to edit your data, this user is allowed to execute all of the following actions:

* edit metadata
* edit styles
* manage styles
* replace layer
* remove layer

To learn how you can edit metadata or change the styles go to this section LINK. 

.. todo:: write a short tutorial on how to edit layers

Maps
----


  

