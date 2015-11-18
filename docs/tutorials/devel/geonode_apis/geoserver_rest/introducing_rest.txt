.. module:: geoserver.introducing_rest
   :synopsis: Learn how to use the GeoServer REST module.

.. _geoserver.rest:

Introducing REST concepts
-------------------------

REST (REpresentational State Transfer) is a simple approach to web services strongly based on the basic 
HTTP infrastructure, such as URLs, HTTP methods and HTTP response codes.

The basic elements of a REST service are:

*  **Resource**: each business entity is linked to a unique URL that represents it, 
   and allows for its retrieval and eventual modification. In GeoServer such resources are layers, stores,
   styles and so on
*  **Connectedness**: the various resources are linked to one another following significant relationships.
   For example, in GeoServer a store contains a list of feature types or coverages, a layer is linked to a 
   style and a feature type/coverage, and so on (in other terms, the set of resources is supposed to 
   be crawable just like a web site).
*  **Representation**: each resource can be represented in one or more way. For example in GeoServer resources
   are normally represented as HTML, XML and JSON.
*  **Stateless-ness**: each communication with the server is atomic and not related to the communications
   happened before or after it. Whatever state needs to be managed needs to be stored as a publicly accessible
   resource.
*  **HTTP methods reuse**: each resource is manipulated via the common HTTP methods each having a common meaning,
   summarized by the following table

  .. list-table:: 
     :widths: 20 80
     :header-rows: 1

     * - **Method**
       - **Description**
     * - GET
       - Retrieves the resource in the specified representation. Query parameters are often used to filter the contents of the returned resource, and sometimes to specify the desired representation format.
     * - HEAD
       - Similar to GET, but instead of returning the full response it returns only the HTTP headers, which might contain information such as the last modification date of the resource
     * - PUT
       - Stores the representation of a resource at a given URL. Used when the client already knows what the final URL of the resource will be
     * - POST
       - Creates a new resource by either getting its contents in the request, or having some parameters to compute it. The main different is that the final URL of the created resource is not known to the client, and is returned by the server after creation via a redirect. It is also used to have the server perform certain actions that cannot be encoded as another method, for example, have it send a SMS (assuming creating a resource representing the SMS is not desirable)
     * - DELETE
       - Destroys the specified resource.

The above results in a web services protocols that is easy to understand, implement and connect to from various
languages, and with good scalability characteristics.

The GeoServer rest interface is located at ``http://localhost:8083/geoserver/rest``, by default a browser will show resources in HTML format allowing for a simple browsable interface to the GeoServer configuration.

   http://localhost:8083/geoserver/rest

   .. figure:: img/rest_browser_1.png

      Browsing the REST interface with HTML format

Follow the links into ``workspaces`` and then ``geosolutions`` and switch the format from ``.html`` to ``xml`` to see the XML representation:

   http://localhost:8083/geoserver/rest/workspaces/geosolutions.xml

   .. figure:: img/rest_browser_2.png

      The GeoSolutions workspace represented as XML
    
