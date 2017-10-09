// shortcuts module
// see http://wiki.openstreetmap.org/wiki/Overpass_turbo/Extended_Overpass_Queries
if (typeof turbo === "undefined") turbo={};
turbo.shortcuts = function(nominatim) {

  if (!nominatim)
    nominatim = turbo.nominatim();
  
  // helpers

  // returns the current visible bbox as a bbox-query
  function map2bbox(lang) {
    var bbox;
    if (!(ide.map.bboxfilter && ide.map.bboxfilter.isEnabled()))
      bbox = ide.map.getBounds();
    else
      bbox = ide.map.bboxfilter.getBounds();
    var lat1 = Math.min(Math.max(bbox.getSouthWest().lat,-90),90);
    var lat2 = Math.min(Math.max(bbox.getNorthEast().lat,-90),90);
    var lng1 = Math.min(Math.max(bbox.getSouthWest().lng,-180),180);
    var lng2 = Math.min(Math.max(bbox.getNorthEast().lng,-180),180);
    if (lang=="OverpassQL")
      return lat1+','+lng1+','+lat2+','+lng2;
    else if (lang=="xml")
      return 's="'+lat1+'" w="'+lng1+'" n="'+lat2+'" e="'+lng2+'"';
  }

  // returns the current visible map center as a coord-query
  function map2coord(lang) {
    var center = ide.map.getCenter();
    if (lang=="OverpassQL")
      return center.lat+','+center.lng;
    else if (lang=="xml")
      return 'lat="'+center.lat+'" lon="'+center.lng+'"';
  }

  // converts relative time to ISO time string
  function relativeTime(instr, callback) {
    var now = Date.now();
    // very basic differential date
    instr = instr.toLowerCase().match(/(-?[0-9]+) ?(seconds?|minutes?|hours?|days?|weeks?|months?|years?)?/);
    if (instr === null) {
      callback(''); // todo: throw an error. do not silently fail
      return;
    }
    var count = parseInt(instr[1]);
    var interval;
    switch (instr[2]) {
      case "second":
      case "seconds":
      interval=1; break;
      case "minute":
      case "minutes":
      interval=60; break;
      case "hour":
      case "hours":
      interval=3600; break;
      case "day":
      case "days":
      default:
      interval=86400; break;
      case "week":
      case "weeks":
      interval=604800; break;
      case "month":
      case "months":
      interval=2628000; break;
      case "year":
      case "years":
      interval=31536000; break;
    }
    var date = now - count*interval*1000;
    callback((new Date(date)).toISOString());
  }

  // geocoded values (object/area ids, coords, bbox)
  function geocodeId(instr, callback) {
    var lang = ide.getQueryLang();
    function filter(n) {
      return n.osm_type && n.osm_id;
    } 
    nominatim.getBest(instr,filter, function(err, res) {
      if (err) return ide.onNominatimError(instr,"Id");
      if (lang=="OverpassQL")
        res = res.osm_type+"("+res.osm_id+")";
      else if (lang=="xml")
        res = 'type="'+res.osm_type+'" ref="'+res.osm_id+'"';
      callback(res);
    });
  }
  function geocodeArea(instr, callback) {
    var lang = ide.getQueryLang();
    function filter(n) {
      return n.osm_type && n.osm_id && n.osm_type!=="node";
    } 
    nominatim.getBest(instr,filter, function(err, res) {
      if (err) return ide.onNominatimError(instr,"Area");
      var area_ref = 1*res.osm_id;
      if (res.osm_type == "way")
        area_ref += 2400000000;
      if (res.osm_type == "relation")
        area_ref += 3600000000;
      if (lang=="OverpassQL")
        res = "area("+area_ref+")";
      else if (lang=="xml")
        res = 'type="area" ref="'+area_ref+'"';
      callback(res);
    });
  }
  function geocodeBbox(instr, callback) {
    var lang = ide.getQueryLang();
    nominatim.getBest(instr, function(err, res) {
      if (err) return ide.onNominatimError(instr,"Bbox");
      var lat1 = Math.min(Math.max(res.boundingbox[0],-90),90);
      var lat2 = Math.min(Math.max(res.boundingbox[1],-90),90);
      var lng1 = Math.min(Math.max(res.boundingbox[2],-180),180);
      var lng2 = Math.min(Math.max(res.boundingbox[3],-180),180);
      if (lang=="OverpassQL")
        res = lat1+','+lng1+','+lat2+','+lng2;
      else if (lang=="xml")
        res = 's="'+lat1+'" w="'+lng1+'" n="'+lat2+'" e="'+lng2+'"';
      callback(res);
    });
  }
  function geocodeCoords(instr, callback) {
    var lang = ide.getQueryLang();
    nominatim.getBest(instr, function(err, res) {
      if (err) return ide.onNominatimError(instr,"Coords");
      if (lang=="OverpassQL")
        res = res.lat+','+res.lon;
      else if (lang=="xml")
        res = 'lat="'+res.lat+'" lon="'+res.lon+'"';
      callback(res);
    });
  }

  return function getShortcuts() {
    var queryLang = ide.getQueryLang();
    return {
      "bbox": map2bbox(queryLang),
      "center": map2coord(queryLang),
      // special handling for global bbox in xml queries (which uses an OverpassQL-like notation instead of n/s/e/w parameters):
      "__bbox__global_bbox_xml__ezs4K8__": map2bbox("OverpassQL"),
      "date": relativeTime,
      "geocodeId": geocodeId,
      "geocodeArea": geocodeArea,
      "geocodeBbox": geocodeBbox,
      "geocodeCoords": geocodeCoords,
      // legacy 
      "nominatimId": queryLang=="xml" ? geocodeId : function(instr,callback) {
        geocodeId(instr, function(result) { callback(result+';'); });
      },
      "nominatimArea": queryLang=="xml" ? geocodeArea : function(instr,callback) {
        geocodeArea(instr, function(result) { callback(result+';'); });
      },
      "nominatimBbox": geocodeBbox,
      "nominatimCoords": geocodeCoords,
    };
  }
};
