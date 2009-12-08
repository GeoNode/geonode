CAPRA GeoNode v0.5
==================

Map Management
==============
* Basic info
  Maps in the GeoNode are saved on the server in a format called JSON.  JSON 
  consists of either lists enclosed by square brackets [] or objects enclosed 
  by curly braces {}.  Inside the brackets, a list is a comma-separated
  sequence of values, while an object is a comma-separated sequence of key- 
  value pairs, with the key delimited from the value by a colon character : . 
  Values can themselves be objects or lists, or they may also be boolean, 
  numeric or string literals.  JSON is discussed in more depth at 
  http://www.json.org/ .

  The JSON for a map in the GeoNode generally follows this format: 
  { about: {
      "title": 'The Map\'s Title',
      "abstract": 'An informative summary of the map\'s content',
      "contact": 'Information about getting in touch with the map\'s creator',
      "featured": false
    },
    wms: {
      "id": "http://host/services/ows",
      "id2": "http://another.host/services/ows"
    },
    map: {
      layers: [ {
          name: "ns:layerid",
          wms: "id",
          group: "background"
      } , {
          name: 'ns2:layerid2",
          wms: "id2"
      } ],
      center: [-84.17, 12.8],
      zoom: 5
    }
  }

  In order, this consists of an "about" object providing metadata about the 
  map, a 'wms' object providing names and service URLs for the WMS services 
  used in the map, and a 'map' object describing the layers and viewport for
  the actual map.  For the most part, these JSON map descriptions are managed 
  automatically by the application.  However, certain administrative tasks 
  require manual manipulation of the maps, stored in individual files within 
  the GeoServer data directory, in a subdirectory called 'json'.  That is, if 
  the GeoServer configuration is in a directory called /var/lib/geoserver_data,
  then the map descriptions are stored in a directory called 
  /var/lib/geoserver_data/json/ .

  You can determine which JSON file corresponds to a particular map by 
  inspecting the 'Permalink' URL offered in the map info page in the viewer.  
  This URL will end with a query string that looks like "?map=abc123", 
  ("?map=" followed by some string of digits and letters).  The string of 
  characters following the "=" sign is the name of the map file in the JSON 
  directory.

* Changing a map from featured to unfeatured (or vice versa)
  After determining a map's filename (described in the previous section), you  
  can change whether it is featured or not by directly editing the JSON file 
  with a text editor such as Notepad.  Find the key labelled 'featured' and set
  it to true to make it featured, or false to take it off of the featured 
  list.  The value must be 'true' or 'false' without quote marks.  If no key 
  called 'featured' is present, you must add it to the 'about' object in order
  to put a map on the featured list.

* Deleting a map
  After determining a map's filename (as described above) you can delete it 
  simply by deleting the file from the directory.

* Setting the featured map on the home page
  In the index.html file, find the line that looks like

  var map = "fxgjt8cv";

  Replace the "fxgjt8cv" string (or whatever it says) with the file name of a map
  in quotes to make that map the featured map of the page.


