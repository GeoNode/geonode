.. module:: geoserver.parameters

.. _geoserver.parameters:


Configuring GeoServer for robustness 
--------------------------------------------------

In a production environment may be necessary to properly configure the WMS service in order to give a limit to resources associated with a request. The **Resource Limits** options allow the administrator to limit the resources consumed by each WMS GetMap request.

GeoServer provides a user interface for these options:


.. figure:: img/parameters1.png
   :align: center
   
   *Setting the Resource consumption limits*


The following table shows each option name, a description, and the minimum GeoServer version at which the option is available (old versions will just ignore it if set).

.. list-table::
   :widths: 10 80 10

   * - **Option**
     - **Description**
     - **Version**
   * - **Max rendering memory**
     - Sets the maximum amount of memory, in kilobytes, a single GetMap request is allowed to use. Each output format will make a best effort attempt to respect the maximum using the highest consuming portion of the request processing as a reference. For example, the PNG output format will take into consideration the memory used to prepare the image rendering surface in memory, usually proportional to the image size multiplied by the number of bytes per pixel
     - 1.7.5
   * - **Max rendering time**
     - Sets the maximum amount of time, in seconds, GeoServer will use to process the request. This time limits the "blind processing" portion of the request serving, that is, the part in which GeoServer is computing the results before writing them out to the client. The portion that     is writing results back to the client is not under the control of this parameter, since this time is also controlled by how fast the network between the server and the client is. So, for example, in the case of PNG/JPEG image generation, this option will control the pure rendering time, but not the time used to write the results back.
     - 1.7.5
   * - **Max rendering errors**
     - Sets the maximum amount of rendering errors tolerated by a GetMap. Usually GetMap skips over faulty features, reprojection errors and the like in an attempt to serve the results anyways. This makes for a best effort rendering, but also makes it harder to spot issues, and consumes CPU cycles as each error is handled and logged
     - 1.7.5
     
Out of the box GeoServer uses 65MB, 60 seconds and 1000 errors respectively. All limits can be disabled by setting their value to ``0``.

Once any of the set limits is exceeded, the GetMap operation will stop and a ``ServiceException`` will be returned to the client.

It is suggested that the administrator sets all of the above limits taking into consideration peak conditions. For example, while a GetMap request under normal circumstance may take less than a second, under high load it is acceptable for it to take longer, but usually, it's not sane that a request goes on for 30 minutes straight. The following table shows some example values for the configuration options above, with explanations of how each is computed:

.. list-table::
   :widths: 20 10 70

   * - **Option**
     - **Value**
     - **Rationale**
   * - maxRequestMemory
     - 65000
     - 65MB are sufficient to render a 4078x4078 image at 4 bytes per pixel (full color and transparency), or a 8x8 meta-tile if you are using GeoWebCache or TileCache. Mind the rendering process will use an extra in memory buffer for each subsequent FeatureTypeStyle in your SLD, so this will also limit the size of the image. For example, if the SLD contains two FeatureTypeStyle element in order to draw cased lines for an highway the maximum image size will be limited to 2884x2884 (the memory goes like the square of the image size, so halving the memory does not halve the image size)
   * - maxRenderingTime
     - 60
     - A request that processes for one minute straight is probably drawing a lot of features independent of the current load. It might be the result of a client making a GetMap against a big layer using a custom style that does not have the proper scale dependencies
   * - maxRenderingErrors
     - 1000
     - Encountering 1000 errors is probably the result of a request that is trying to reproject a big data set into a projection that is not suited to area it covers, resulting in many reprojection failures.

