.. _layers.share:

Sharing layers
==============

GeoNode has the ability to restrict or allow other users to access a layer and share on social media.

Anonymous access
----------------

#. Go to the layer preview of the first layer uploaded, and copy the URL to that preview page.

   .. note:: The URL should be something like: ``http://GEONODE/layers/geonode:san_andres_y_providencia_administrative``

#. Now log out of GeoNode by clicking on your profile name and selecting :guilabel:`Log out`.

   .. figure:: img/logoutlink.png

      *Log out*

#. When asked for confirmation, click the :guilabel:`Log out` button.

   .. figure:: img/logoutconfirm.png

      *Confirming log out*

#. Now paste the URL copied about into your browser address bar and navigate to that location.

#. You will be redirected to the Log In form. This is because when this layer was first uploaded, we set the view properties to be any registered user. Once logged out, we are no longer a registered user and so are not able to see or interact with the layer, unless we log in GeoNode again.

   .. figure:: img/forbidden.png

      *Unable to view this protected layer*

#. To stop this process from happening, you need to ensure that your permissions are set so *anyone* can view the layer for others to see it on social networks. 

.. figure:: img/map_permissions.png

#. This is done by selecting *anyone* in the layer permissions tab, be aware this now means your layer is public!

Sharing with social media
-------------------------

#. On the taskbar below your username and profile picture there are three links to social media services, Twitter, Google Plus and Facebook.

   .. figure:: img/socialmedia.png

#. Upon clicking on these icons you will be taken through the application's process for posting to the social network.  Ensure the permissions are set so *anyone* can view the layer if you want unauthenticated to be able to access it.
