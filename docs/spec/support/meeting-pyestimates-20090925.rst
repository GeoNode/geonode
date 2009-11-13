====================================
MyHazard and Safe Hospitals Django Component Estimation
====================================

Apps
====


geonode.core -- 
capra.site -- Basic navigation for CAPRA GeoNode
capra.myhazards -- handles the MyHazards application
capra.safehospitals -- depends on GeoNode.hazards

(geonode.site -- some unthemed basic nav for geonode.core)


Q: How do we make the site navigation (tabs) work in a pluggable way? Do we do this now?


capra.myhazards
===============

Views
-----

* Layout View
 - template for setting up the javascript/client
 - includes configuration: [Note: in the current tspec, this is listed as a REST API, it need not be REST since it's just going to be in the view response]
   - which layers are hazard layers
   - what periods they represent
   - what hazards each layer is in
(in the current tech spec this is inverted, rightly)
  - internationalization for both JS and the HTML template

* Report Summary Handler: /hazard/report.html?what=haveyou
 - takes a location, list of active layers, and viewport information from client
 - queries geoserver for data with:
     * location
     * list of hazard/period layers
     * radius
 - parses returned data, which includes:
     * mean, median, standard deviation, range for each layer
     * some political data (country, municipality ??) for the point of interest
 - generates html return for client popup
  - django templates to generate the HTML with:
   - info about radius used for report
   - data from summary service
   - download link for PDF

- if error: formatted error message for popup

 Q: What do the radiuses really depend?


* PDF Report Handler /hazard/report.pdf?what=haveyou
 - takes same query as summary handler
 - queries geoserver
 - geoserver returns
  - data 
  - multiple images from WMS requests (owslib)
 - view formats data and images and uses reportlab to create PDF
   http://docs.djangoproject.com/en/dev/howto/outputting-pdf/
 - i18n
  - static disclaimer text etc. in templates
 - Error handling (in case, say, GeoServer barfs during the WMS)
  
  
 Q: Does disclaimer text need to be specified when data is uploaded?  Is it constant per hazard, or per period, or per anything useful. 
 Q: What's up with binned data?


 
Models (Category App)
---------------------

Hazard: A type of hazard (such as storm surge or landslides). Each Hazard contains the following fields:
- name
the display name to use for the hazard grouping in user interface elements
and is associated with multiple Period records and multiple RadiusInfo records.

Period: A range of time over which data is aggregated.  Each Period contains the following fields:
- typename
The single typename for the coverage layer containing the data for the given hazard and period. This is currently a string (assumed to be hosted by the GeoServer that accompanies the GeoNode) but might be changed to reference some Layer type in the future.
- length
The duration of the period, measured in years.
Each Period is related to a single Hazard record.

RadiusInfo: A mapping from a range of scale denominator values to the real-world radius of the area across which data should be collected for the reporting application.  Each RadiusInfo contains the following fields:
- minscale
The minimum scale denominator (inclusive) of the range where this radius is applicable.
- maxscale
The maximum scale denominator (exclusive) of the range where this radius is applicable.
- radius
The radius in meters of the buffer to apply when gathering report data in the given scale range.
Each RadiusInfo is related to a single Hazard record.


Admin
-----

Django admin + some.

Q. how much input for something like radiuses.




geonode.core
============

Map Browsing Tab
 - REST API
 - Some client work to make the app fit the REST API

Internationalization port

(maybe not needed for feature parity)
Layer Model
 - some flag for "local"
 - use it in Hazard configuration (in place of typename in the Period model)
 - use it in the (renamed) Layer model in the map management model
 
 
 
capra.safehospitals
===================

View
----

* Layout view
  - serves some HTML and JavaScript 
  [client handles everything -- generating HTML for any popup needed based on feature attributes]
 
* [later] PDF Hazard Report Handler
 - takes a location, [no list of active layers--Django has this], and viewport information from client
 - generates PDF report like in MyHazard
 - but potentially with a little bit of Hospital-specific data in the report.
   - the request PDF Hazard Report view contains feature id of the hospital that we are reporting on.
     - Django uses the Hospital Layer Name and feature id to get the hospital data from GeoServer using WFS.
 - maybe some Safe Hospitals specific disclaimer/informative text.


Configuration
-------------

- Hospital layer

This is Django configuration file.  Which layer is the hospitals layer?




Site Integration
----------------

* Client win to do i18n in django
* 
