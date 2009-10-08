Data Aggregation
================

Once the user has customized his map view and selected his point of interest,
the server must go to work collecting and summarizing data to put into the
report.  This will be implemented as a WPS process incorporating the following
parameters:

* ReportGeometry: a geometry (for the purposes of this round, a point) about
  which the summary is generated.
* BufferSize: a buffer size which expands the input geometry.  The summary
  consists of some statistics gathered across the coverage values within this
  buffered geometry
* LayersOfInterest: a list of layers across which statistics are gathered

.. todo:: 

    Verify that these parameters are sufficient to fill out the report data.

The Process
-----------

In rough pseudo-code, the summary process will look like::

    def process(geom, radius, layers): 
        buffered = doBuffer(geom, radius)
        stats = {}

        for layer in layers:
            data_chunk = layer.intersect(buffered)
            if not empty(data_chunk): 
                stats[layer.name] = [
                    min(data_chunk),
                    max(data_chunk),
                    mean(data_chunk),
                    std_dev(data_chunk)
                ])

        political_data = CONFIG.POLITICAL_DATASET
        political = []

        for (record in political_data.query("geometry intersects " + buffered):
            political.extend({
               "country": record["country"],
               "municipality": record["municipality"]
            })
            
        political = political_data.query("geometry intersects " + buffered)

        return stats, political
        
REST Encapsulation
------------------

Rather than implement a WPS client for this application, it has been proposed
that we create a REST endpoint that performs the WPS operation for us and
provides a simplified response.  The goal would be to investigate options for
creating something reusable for others who "just want to do some processing"
and don't require the full power and abstraction of WPS.

There will be a single endpoint for this REST service, at
:file:`/rest/process/hazardsummary`.  Requests and responses will be formatted
in JSON.  A client initiates a summary process by POSTing to the REST service::
    
    {
        "radius": 12,
        "geometry": {
            "type": "Feature",
            "id": "OpenLayers.Feature.Vector_192",
            "properties": {
            },
            "geometry": {
                "type": "Point",
                "coordinates": [13, 22]
            },
            "crs": {
                "type": "OGC",
                "properties": {
                    "urn": "urn:ogc:def:crs:OGC:1.3:CRS84"
                }
            }
        },
        "layers": [
            "zombie:attacks_10y",
            "candy:drought_2y"
        ]
    }
    
After crunching the appropriate numbers, the server responds with::
   
    {
        "statistics": {
            "zombie:attacks_10y": [3, 5, 4, 1],
            "candy:drought_2y": [1, 10, 5.5, 4]
        },
        "political": [{
            "country": "Nicaragua",
            "municipality": "Hometown"
        }]
    }

.. note:: 

    The numbers in these examples are not intended to be mathematically
    consistent and only serve to demonstrate the data format.
