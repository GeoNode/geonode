Configuration Geonode 2.0
-------------------------

**Step 1 - Create a superuser**

After succesfully installing Geonode 2.0 it is recommended to create a superuser. This one you will need to login into Geonode, upload data and create maps.
For the creation of a superuser your virtual environment of geonode has to be active. How to do this is explained above in Step a - Activate geonode virtualenv.

Now you have activated the virtual environment you can type the following into your terminal:

    django-admin.py createsuperuser –-settings=geonode.settings

and you will be asked for a username, an email-adress and a password. 
