Report Templating
=================

For the purposes of our application, we will require at least two "classes" of
report: 

* a lightweight format suitable for insertion into an HTML page (the use
  case being a popup or other transient view in a slippy map on the web)
* a more heavily themed format suitable for download as a PDF (presumably for
  later printing by the user)

In order to accommodate sharing of the data access code between both classes of
template, both the HTML and PDF reports will be generated through Django views.

.. _html-report:

HTML
----

The HTML output will be generated via a standard Django template.

.. seealso:: 

    The functional specification for information about the formatting of this
    report.


.. seealso:: 

    :doc:`/reporting-application/data-aggregation` for discussion of the
    contents of the WPS response

PDF
---

The PDF template will be implemented as a Django route using the 
`ReportLab <http://reportlab.org/>`_ Python module.

This entails: 

1. Implement a "map" flowable that allows us to pull map tiles into the PDF
   document.  This block should be sufficiently parametrized that we can easily
   choose which layers are included and specify the area of interest.  

2. Create a report layout function that makes the appropriate rendering calls
   to create the report.  We should be able to use the Platypus layout engine
   (included with ReportLab) to structure this document, manage overflow onto
   new pages, etc.
