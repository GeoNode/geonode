Checklist
=========

UI
--

* ~~resizable panels (editor/map)- maybe also: hide editor temporarily for map inspections (or just go with a fullscreen mode?)~~
* ~~editor: better Syntax highlighting (auto detect query language xml/overpassQL, support for overpassQL)~~
* editor: code auto completion (with inline help?) ~~and auto tag closing for xml~~
* ~~editor: highline lines where an error occured~~
* map: make crosshairs not overlap map popups
* ~~map: make crosshairs optional (default: not visible)~~
* map popups: ~~show coordinates of points~~ (and bbox of ways?), ~~show metadata (if present)~~
* ~~tool: convert overpassql<->xml~~
* ? better layer management: allow multiple layers to be set up (if #layers>1 show layer switcher). allow also other types of layers (WMS, ImageOverlay?)
* ~~wide map view~~
* ~~make UI texts translatable~~
* ~~export: to-josm should print a warning, when data is not in XML+meta format.~~
* editor: pretty-print on button press
* editor: highlighting of structural elements?
* editor: ~~tooltips~~ , inline help
* editor: syntax check on button press
* ~~map: reset data~~
* ~~implement short url generator~~
* ~~disable "start at current pos" by default~~
* ~~implement auto-correct for queries returning no nodes by adding recurse statements~~
* ~~fix for disappearing line and polygon features at low zoom.~~
* ~~print number of found elements (pois, ways, polygons)~~
* ~~add "map key" to help~~
* ~~add templates~~
* rendering GeoJSON: sort polygons by area (or simply bbox area), such that smaller polygons are drawn over large ones.
* export as png: render scale & attribution separately, and blend in after the data overlay
* OSM4Leaflet: add "context" callback instead of hardcoded magic
* ~~open external links in new tabs!~~
* ~~show warning when there are large amounts of data to be loaded (>10.000, >100.000 nodes? or in MBytes of data?)~~
* do not apply novanish when a way is member of route/multipolygon (more?) relations.
* share tool: add forumish / markdown / etc. links
* share tool: add embed as html (= map.html export)
* ~~support for osm-style lat/lon/zoom parameters~~
* autorun queries if code+location+zoom is supplied in the url??
* ~~do not auto-show help if the page was started via share-link, template, etc.?? or begin with a shorter, very general welcome dialog (linking to help for example)~~
* ~~mark finished items by a check-mark.~~
* implement poly-boundings selector (I may have to wait for the most recent leaflet-draw plugin) 
* ~~deactivate "manually select bbox" when there is no "{{bbox}}" in the query.~~
* ~~add description on how to run templates (e.g. "select region in the map and hit run").~~
* ~~rename Export->Query->XML. e.g. "Overpass-XML query"~~
* ~~add Export->Data->OSM-Data (like the data tab).~~
* ~~exclude internal variables (like mp_outline, tainted, etc.) from direct geoJSON output (better: put into meta data object?)~~

MapCSS
------
* do not requery Overpass API if the query (incl. bbox) did not change between 2 "RUN"s and there is not much time in between?
* add keyboard shortcut for only reapplying styles
* implement text/label properties of mapcss
* implement other symbol-shapes (square, triangle, marker, etc.)
* implement line casings, shields
* let the background tiles be set by something like 'canvas { background-tiles:"..."; background-opacity:1; background-overlays:"...;...;..."; }'