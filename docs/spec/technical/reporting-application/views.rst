Django Views
============

On the Django side, the following views will be required:

:file:`/hazard/`
    Presents the HTML housing the :doc:`JavaScript reporting application
    </reporting-application/frontend>`.

    This view will need to provide:

        * Site branding
        * Application-specific scripts and styles
        * Configuration for the reporting application 

          .. seealso:: :doc:`/reporting-application/category-application`

        * i18n values for the JavaScript components and HTML template.

:file:`/hazard/report.html`
    Fetches report data and converts it to an HTML snippet suitable for use by
    the reporting application's preview feature.

    This view will need to provide:
        * handling of query parameters sent by the JavaScript application
            
            - location
            - active layers
            - zoom level

        * formatting those parameters into a request to GeoServer

            - location
            - active layers
            - radius

        * parsing of the results of that request to GeoServer
          
            - statistics (mean, median, standard deviation, range) for each
              layer
            - political/context information (country, municipality, etc.) for
              the point of interest

        * interpolation of the report data into a Django template
        * proper error handling (an HTML error report) if

            - GeoServer doesn't give back the expected response
            - the request parameters don't conform to the expected set

:file:`/hazard/report.pdf`
    Fetches the report data and converts it to a PDF document suitable for
    downloading, printing, and attaching to corporate refrigerators.

    This view will need to provide:
        * handling of query parameters, formatting, parsing, error reporting
          similar to that done by the HTML report view
        * interpolation of the report data into a ReportLab document. In
          addition to the data included in the HTML report, this report will
          include:

            - WMS tiles for each reported layer
            - Internationalized disclaimer text about the suitability for usage
              of the data
            - (Possibly) charts of the statistics

