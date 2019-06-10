Using Remote Services
=====================

In GeoNode you can add new layers not only loading them from your disk but also using *Remote Services*. In this section you will learn how to add a new service and how to load resources in GeoNode through that.

Let's try it!

Click on the :guilabel:`Remote Services` link of the :guilabel:`Data` menu in the navigation bar.

.. figure:: img/remote_services_link.png
    :align: center

    *Remote Services link*

The page that opens will contain the list of the available services.

.. figure:: img/remote_services.png
    :align: center

    *Remote Services*

To configure a new service:

* click on :guilabel:`Register a new Service`
* type the *Service URL*
* select the *Service Type*

  .. figure:: img/service_type.png
      :align: center

      *Service Types*

* click on :guilabel:`Create`

.. note:: Lots of services are available on the internet, in this example we used the ``https://demo.geo-solutions.it/geoserver/wms``.

Once the service has been configured, you can load the resources you are interested in through the *Import Resources* page where you will be automatically redirected to. Take a look at the gif below to see the whole process.

.. figure:: img/new_remote_service.gif
    :align: center

    *A new Remote Servce*

| From the page where the services are listed, it is possible to click on the *Title* of a service. It opens the *Service Details* page.
| Each service has its own metadata such as the *Service Type*, the *URL*, an *Abstract*, some *Keywords* and the *Contact* user. You can edit those metadata through the form available from the :guilabel:`Edit Service Metadata` button of the *Service Details* page (see the picture below).

.. figure:: img/remote_service_metadata.png
    :align: center

    *Remote Servce metadata*
