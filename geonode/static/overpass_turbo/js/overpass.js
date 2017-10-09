
// global overpass object

var overpass = new(function() {
  // == private members ==
  var originalGeom2Layer;
  // == public members ==
  this.handlers = {};

  // == private methods ==
  var fire = function() {
    var args = fire.arguments;
    var name = args[0];
    if (typeof overpass.handlers[name] != "function")
      return undefined;
    var handler_args = [];
    for (var i=1; i<args.length; i++) 
      handler_args.push(args[i]);
    return overpass.handlers[name].apply({},handler_args);
  }

  // == public methods ==

  this.init = function() {
    // register mapcss extensions
    /* own MapCSS-extension:
     * added symbol-* properties
     * TODO: implement symbol-shape = marker|square?|shield?|...
     */
    styleparser.PointStyle.prototype.properties.push('symbol_shape','symbol_size','symbol_stroke_width','symbol_stroke_color','symbol_stroke_opacity','symbol_fill_color','symbol_fill_opacity');
    styleparser.PointStyle.prototype.symbol_shape = "";
    styleparser.PointStyle.prototype.symbol_size = NaN;
    styleparser.PointStyle.prototype.symbol_stroke_width = NaN;
    styleparser.PointStyle.prototype.symbol_stroke_color = null;
    styleparser.PointStyle.prototype.symbol_stroke_opacity = NaN;
    styleparser.PointStyle.prototype.symbol_fill_color = null;
    styleparser.PointStyle.prototype.symbol_fill_opacity = NaN;

    // prepare some Leaflet hacks
    originalGeom2Layer = L.GeoJSON.geometryToLayer;
  }

  // updates the map
    this.run_query = function (query, query_lang, cache, shouldCacheOnly) {
    var server = (ide.data_source && 
                  ide.data_source.mode == "overpass" &&
                  ide.data_source.options.server) ?
                 ide.data_source.options.server : settings.server;
    // 1. get overpass json data
    if (query_lang == "xml") {
      // beautify not well formed xml queries (workaround for non matching error lines)
      if (!query.match(/^<\?xml/)) {
        if (!query.match(/<osm-script/))
          query = '<osm-script>'+query+'</osm-script>';
        query = '<?xml version="1.0" encoding="UTF-8"?>'+query;
      }
    }
    fire("onProgress", "calling Overpass API interpreter", function(callback) {
      // kill the query on abort
      overpass.ajax_request.abort();
      // try to abort queries via kill_my_queries
      $.get(server+"kill_my_queries").success(callback).error(function() {
        console.log("Warning: failed to kill query.");
        callback();
      });
    });
    var request_headers = {};
    var additional_get_data = "";
    if (settings.force_simple_cors_request) {
      additional_get_data = "?X-Requested-With="+configs.appname;
    } else {
      request_headers["X-Requested-With"] = configs.appname;
    }
    var onSuccessCb = function(data, textStatus, jqXHR) {
      //textStatus is not needed in the successCallback, don't cache it
      if (cache) cache[query] = [data, undefined, jqXHR];

      var data_amount = jqXHR.responseText.length;
      var data_txt;
      // round amount of data
      var scale = Math.floor(Math.log(data_amount)/Math.log(10));
      data_amount = Math.round(data_amount / Math.pow(10,scale)) * Math.pow(10,scale);
      if (data_amount < 1000)
        data_txt = data_amount + " bytes";
      else if (data_amount < 1000000)
        data_txt = data_amount / 1000 + " kB";
      else
        data_txt = data_amount / 1000000 + " MB";
      fire("onProgress", "received about "+data_txt+" of data");
      fire("onDataRecieved", data_amount, data_txt, 
      function() { // abort callback
        fire("onAbort");
        return;
      }, function() { // continue callback
      // different cases of loaded data: json data, xml data or error message?
      var data_mode = null;
      var geojson;
      var stats = {};
      fire("onProgress", "parsing data");
setTimeout(function() {
       // hacky firefox hack :( (it is not properly detecting json from the content-type header)
      if (typeof data == "string" && data[0] == "{") { // if the data is a string, but looks more like a json object
        try {
          data = $.parseJSON(data);
        } catch (e) {}
      }
      // hacky firefox hack :( (it is not properly detecting xml from the content-type header)
      if (typeof data == "string" && data.substr(0,5) == "<?xml" && jqXHR.status === 200 && !(jqXHR.getResponseHeader("content-type") || "").match(/text\/html/) && data.match(/<osm/)) {
        try {
          jqXHR.responseXML = data;
          data = $.parseXML(data);
        } catch (e) {
          delete jqXHR.responseXML;
        }
      }
      if ((typeof data == "string") ||
          (typeof data == "object" && jqXHR.responseXML && $("remark",data).length > 0) ||
          (typeof data == "object" && data.remark && data.remark.length > 0)
          ) { // maybe an error message
        data_mode = "unknown";
        var is_error = false;
        is_error = is_error || (typeof data == "string" && // html coded error messages
          data.indexOf("Error") != -1 && 
          data.indexOf("<script") == -1 && // detect output="custom" content
          data.indexOf("<h2>Public Transport Stops</h2>") == -1); // detect output="popup" content
        is_error = is_error || (typeof data == "object" &&
          jqXHR.responseXML &&
          $("remark",data).length > 0);
        is_error = is_error || (typeof data == "object" &&
          data.remark &&
          data.remark.length > 0);
        if (is_error) {
          // this really looks like an error message, so lets open an additional modal error message
          var errmsg = "?";
          if (typeof data == "string") {
            errmsg = data.replace(/([\S\s]*<body>)/,"").replace(/(<\/body>[\S\s]*)/,"");
            // do some magic cleanup for better legibility of the actual error message
            errmsg = errmsg.replace(/<p>The data included in this document is from .*?<\/p>/,"");
            var fullerrmsg = errmsg;
            errmsg = errmsg.replace(/open64: 0 Success \/osm3s_v\d+\.\d+\.\d+_osm_base (\w+::)*\w+\./,"[…]");
          }
          if (typeof data == "object" && jqXHR.responseXML)
            errmsg = "<p>"+$.trim($("remark",data).text())+"</p>";
          if (typeof data == "object" && data.remark)
            errmsg = "<p>"+$.trim(data.remark)+"</p>";
          console.log("Overpass API error", fullerrmsg || errmsg); // write (full) error message to console for easier debugging
          fire("onQueryError", errmsg);
          data_mode = "error";
          // parse errors and highlight error lines
          var errlines = errmsg.match(/line \d+:/g) || [];
          for (var i=0; i<errlines.length; i++) {
            fire("onQueryErrorLine", 1*errlines[i].match(/\d+/)[0]);
          }
        }
        // the html error message returned by overpass API looks goods also in xml mode ^^
        overpass.resultType = "error";
        data = {elements:[]};
        overpass.timestamp = undefined;
        overpass.timestampAreas = undefined;
        overpass.copyright = undefined;
        stats.data = {nodes: 0, ways: 0, relations: 0, areas: 0};
        //geojson = [{features:[]}, {features:[]}, {features:[]}];
      } else if (typeof data == "object" && jqXHR.responseXML) { // xml data
        overpass.resultType = "xml";
        data_mode = "xml";
        overpass.timestamp = $("osm > meta:first-of-type",data).attr("osm_base");
        overpass.timestampAreas = $("osm > meta:first-of-type",data).attr("areas");
        overpass.copyright = $("osm > note:first-of-type",data).text();
        stats.data = {
          nodes:     $("osm > node",data).length,
          ways:      $("osm > way",data).length,
          relations: $("osm > relation",data).length,
          areas:     $("osm > area",data).length
        };
        //// convert to geoJSON
        //geojson = overpass.overpassXML2geoJSON(data);
      } else { // maybe json data
        overpass.resultType = "javascript";
        data_mode = "json";
        overpass.timestamp = data.osm3s.timestamp_osm_base;
        overpass.timestampAreas = data.osm3s.timestamp_areas_base;
        overpass.copyright = data.osm3s.copyright;
        stats.data = {
          nodes:     $.grep(data.elements, function(d) {return d.type=="node"}).length,
          ways:      $.grep(data.elements, function(d) {return d.type=="way"}).length,
          relations: $.grep(data.elements, function(d) {return d.type=="relation"}).length,
          areas:     $.grep(data.elements, function(d) {return d.type=="area"}).length,
        };
        //// convert to geoJSON
        //geojson = overpass.overpassJSON2geoJSON(data);
      }

      //fire("onProgress", "applying styles"); // doesn't correspond to what's really going on. (the whole code could in principle be put further up and called "preparing mapcss styles" or something, but it's probably not worth the effort)
setTimeout(function() {
      // test user supplied mapcss stylesheet
      var user_mapcss = ide.mapcss; 
      try {
        var dummy_mapcss = new styleparser.RuleSet();
        dummy_mapcss.parseCSS(user_mapcss);
        try {
          dummy_mapcss.getStyles({
            isSubject:function() {return true;},
            getParentObjects: function() {return [];},
          }, [], 18);
        } catch(e) {
          throw new Error("MapCSS runtime error.");
        }
      } catch(e) {
        user_mapcss = "";
        fire("onStyleError", "<p>"+e.message+"</p>");
      }
      var mapcss = new styleparser.RuleSet();
      mapcss.parseCSS(""
        +"node, way, relation {color:black; fill-color:black; opacity:1; fill-opacity: 1; width:10;} \n"
        // point features
        +"node {color:#03f; width:2; opacity:0.7; fill-color:#fc0; fill-opacity:0.3;} \n"
        // line features
        +"line {color:#03f; width:5; opacity:0.6;} \n"
        // polygon features
        +"area {color:#03f; width:2; opacity:0.7; fill-color:#fc0; fill-opacity:0.3;} \n"
        // style modifications
        // objects in relations
        +"relation node, relation way, relation {color:#d0f;} \n"
        // tainted objects
        +"way:tainted, relation:tainted {dashes:5,8;} \n"
        // placeholder points
        +"way:placeholder, relation:placeholder {fill-color:#f22;} \n"
        // highlighted features
        +"node:active, way:active, relation:active {color:#f50; fill-color:#f50;} \n"
        // user supplied mapcss
        +user_mapcss
      );
      var get_feature_style = function(feature, highlight) {
        function hasInterestingTags(props) {
          // this checks if the node has any tags other than "created_by"
          return props && 
                  props.tags && 
                  (function(o){for(var k in o) if(k!="created_by"&&k!="source") return true; return false;})(props.tags);
        }
        var s = mapcss.getStyles({
          isSubject: function(subject) {
            switch (subject) {
              case "node":     return feature.properties.type == "node" || feature.geometry.type == "Point";
              case "area":     return feature.geometry.type == "Polygon" || feature.geometry.type == "MultiPolygon";
              case "line":     return feature.geometry.type == "LineString";
              case "way":      return feature.properties.type == "way";
              case "relation": return feature.properties.type == "relation";
            }
            return false;
          },
          getParentObjects: function() {
            if (feature.properties.relations.length == 0)
              return [];
            else
              return feature.properties.relations.map(function(rel) {
                return {
                  tags: rel.reltags,
                  isSubject: function(subject) {
                    return subject=="relation" || 
                            (subject=="area" && rel.reltags.type=="multipolyon");
                  },
                  getParentObjects: function() {return [];},
                }
              });
          } 
        }, $.extend(
          feature.properties && feature.properties.tainted ? {":tainted": true} : {},
          feature.properties && feature.properties.geometry ? {":placeholder": true} : {},
          feature.is_placeholder ? {":placeholder": true} : {},
          hasInterestingTags(feature.properties) ? {":tagged":true} : {":untagged": true},
          highlight ? {":active": true} : {},
          feature.properties.tags)
        , 18 /*restyle on zoom??*/);
        return s;
      };

      L.GeoJSON.geometryToLayer = function(feature, pointToLayer /*,…*/) {
        var s = get_feature_style(feature);
        var stl = s.textStyles["default"] || {};
        var layer = originalGeom2Layer.apply(this, arguments);

        var latlng;
        if (feature.geometry.type=="Point") {
          latlng = layer.getLatLng();
        } else if (feature.geometry.type=="Polygon") {
          latlng = layer.getBounds().getCenter();
        } else if (feature.geometry.type=="MultiPolygon") {
          latlng = layer.getLayers()[0].getBounds().getCenter();
        } else if (feature.geometry.type=="LineString") {
          var latlngs = layer.getLatLngs();
          if (latlngs.length % 2 == 1)
            latlng = latlngs[Math.floor(latlngs.length/2)];
          else {
            var latlng1 = latlngs[Math.floor(latlngs.length/2)],
                latlng2 = latlngs[Math.floor(latlngs.length/2-1)];
            latlng = L.latLng([ (latlng1.lat+latlng2.lat)/2, (latlng1.lng+latlng2.lng)/2 ]);
          }
        } // todo: multilinestrings, multipoints
        if (stl["text"] && (text = feature.properties.tags[stl["text"]])) {
          var textIcon = new L.PopupIcon(htmlentities(text), {color: "rgba(255,255,255,0.8)"});
          var textmarker = new L.Marker(latlng, {icon: textIcon});
          return new L.FeatureGroup(_.compact([layer, textmarker]));
        }
        return layer;
      }
      //overpass.geojsonLayer = 
        //new L.GeoJSON(null, {
        //new L.GeoJsonNoVanish(null, {
      overpass.osmLayer =
        new L.OSM4Leaflet(null, {
        afterParse: function() {fire("onProgress", "rendering geoJSON");},
        baseLayerClass: settings.disable_poiomatic ? L.GeoJSON : L.GeoJsonNoVanish,
        baseLayerOptions: {
        threshold: 9*Math.sqrt(2)*2,
        compress: function(feature) {
          return true;
        },
        style: function(feature, highlight) {
          var stl = {};
          var s = get_feature_style(feature, highlight);
          // apply mapcss styles
          function get_property(styles, properties) {
            for (var i=properties.length-1; i>=0; i--)
              if (styles[properties[i]] !== undefined) return styles[properties[i]];
            return undefined;
          }
          switch (feature.geometry.type) {
            case "Point":
              var styles = $.extend({},s.shapeStyles["default"],s.pointStyles["default"]);
              var p = get_property(styles, ["color","symbol_stroke_color"]);
              if (p !== undefined) stl.color       = p;
              var p = get_property(styles, ["opacity","symbol_stroke_opacity"]);
              if (p !== undefined) stl.opacity     = p;
              var p = get_property(styles, ["width","symbol_stroke_width"]);
              if (p !== undefined) stl.weight      = p;
              var p = get_property(styles, ["fill_color", "symbol_fill_color"]);
              if (p !== undefined) stl.fillColor   = p;
              var p = get_property(styles, ["fill_opacity", "symbol_fill_opacity"]);
              if (p !== undefined) stl.fillOpacity = p;
              var p = get_property(styles, ["dashes"]);
              if (p !== undefined) stl.dashArray   = p.join(",");
              break;
            case "LineString":
              var styles = s.shapeStyles["default"];
              var p = get_property(styles, ["color"]);
              if (p !== undefined) stl.color       = p;
              var p = get_property(styles, ["opacity"]);
              if (p !== undefined) stl.opacity     = p;
              var p = get_property(styles, ["width"]);
              if (p !== undefined) stl.weight      = p;
              var p = get_property(styles, ["offset"]);
              if (p !== undefined) stl.offset      = -p; // MapCSS and PolylineOffset definitions use different signs
              var p = get_property(styles, ["dashes"]);
              if (p !== undefined) stl.dashArray   = p.join(",");
            break;
            case "Polygon":
            case "MultiPolygon":
              var styles = s.shapeStyles["default"];
              var p = get_property(styles, ["color","casing_color"]);
              if (p !== undefined) stl.color       = p;
              var p = get_property(styles, ["opacity","casing_opacity"]);
              if (p !== undefined) stl.opacity     = p;
              var p = get_property(styles, ["width","casing_width"]);
              if (p !== undefined) stl.weight      = p;
              var p = get_property(styles, ["fill_color"]);
              if (p !== undefined) stl.fillColor   = p;
              var p = get_property(styles, ["fill_opacity"]);
              if (p !== undefined) stl.fillOpacity = p;
              var p = get_property(styles, ["dashes"]);
              if (p !== undefined) stl.dashArray   = p.join(",");
            break;
          }
          // todo: more style properties? linecap, linejoin?
          // return style object
          return stl;
        },
        pointToLayer: function (feature, latlng) {
          // todo: labels!
          var s = get_feature_style(feature);
          var stl = s.pointStyles["default"] || {};
          var text;
          var marker;
          if (stl["icon_image"]) {
            // return image marker
            var iconUrl = stl["icon_image"].match(/^url\(['"](.*)['"]\)$/)[1];
            var iconSize;
            if (stl["icon_width"]) iconSize=[stl["icon_width"],stl["icon_width"]];
            if (stl["icon_height"] && iconSize) iconSize[1] = stl["icon_height"];
            var icon = new L.Icon({
              iconUrl: iconUrl,
              iconSize: iconSize,
              // todo: anchor, shadow?, ...
            });
            marker = new L.Marker(latlng, {icon: icon});
          } else if (stl["symbol_shape"]=="none") {
            marker = new L.Marker(latlng, {icon: new L.DivIcon({iconSize: [0,0], html: "", className: "leaflet-dummy-none-marker"})});
          } else if (stl["symbol_shape"]=="circle" || true /*if nothing else is specified*/) {
            // return circle marker
            var r = stl["symbol_size"] || 9;
            marker = new L.CircleMarker(latlng, {
              radius: r,
            });
          }
          return marker;
        },
        onEachFeature : function (feature, layer) {
          layer.on('click', function(e) {
            var popup = "";
            if (feature.properties.type == "node")
              popup += "<h2>Node <a href='//www.openstreetmap.org/node/"+feature.properties.id+"' target='_blank'>"+feature.properties.id+"</a></h2>";
            else if (feature.properties.type == "way")
              popup += "<h2>Way <a href='//www.openstreetmap.org/way/"+feature.properties.id+"' target='_blank'>"+feature.properties.id+"</a></h2>";
            else if (feature.properties.type == "relation")
              popup += "<h2>Relation <a href='//www.openstreetmap.org/relation/"+feature.properties.id+"' target='_blank'>"+feature.properties.id+"</a></h2>";
            else
              popup += "<h2>"+feature.properties.type+" #"+feature.properties.id+"</h2>";
            if (feature.properties && feature.properties.tags && !$.isEmptyObject(feature.properties.tags)) {
              popup += '<h3>Tags:</h3><ul class="plain">';
              $.each(feature.properties.tags, function(k,v) {
                k = htmlentities(k); // escaping strings!
                v = htmlentities(v);
                // hyperlinks for http,https and ftp URLs
                var url;
                if (url = v.match(/\b((?:(https?|ftp):\/\/|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}\/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’]))/gi)) {
                  url = url[0];
                  var href = url.match(/^(https?|ftp):\/\//) ? url : 'http://'+url;
                  v = '<a href="'+href+'" target="_blank">'+url+'</a>'
                } else {
                  // hyperlinks for email adresses
                  v = v.replace(/(([^\s()<>]+)@([^\s()<>]+[^\s`!()\[\]{};:'".,<>?«»“”‘’]))/g,'<a href="mailto:$1" target="_blank">$1</a>');
                }
                // hyperlinks for wikipedia entries
                var wiki_lang, wiki_page;
                if (((wiki_lang = k.match(/^wikipedia\:(.*)$/)) && (wiki_page = v)) || 
                    ((k == "wikipedia") && (wiki_lang = v.match(/^([a-zA-Z]+)\:(.*)$/)) && (wiki_page = wiki_lang[2])))
                  v = '<a href="//'+wiki_lang[1]+'.wikipedia.org/wiki/'+encodeURIComponent(wiki_page)+'" target="_blank">'+v+'</a>';
                // hyperlinks for wikidata entries
                var wikidata_page;
                if (((k == "wikidata") && (wikidata_page = v.match(/^Q[0-9]+$/))) ||
                    (k.match(/:wikidata$/) && (wikidata_page = v.match(/^Q[0-9]+$/))))
                  v = '<a href="//www.wikidata.org/wiki/'+encodeURIComponent(wikidata_page[0])+'" target="_blank">'+v+'</a>';
                popup += "<li>"+k+"="+v+"</li>"
              });
              popup += "</ul>";
            }
            if (feature.properties && feature.properties.relations && !$.isEmptyObject(feature.properties.relations)) {
              popup += '<h3>Relations:</h3><ul class="plain">';
              $.each(feature.properties.relations, function (k,v) {
                popup += "<li><a href='//www.openstreetmap.org/relation/"+v["rel"]+"' target='_blank'>"+v["rel"]+"</a>";
                if (v.reltags && 
                    (v.reltags.name || v.reltags.ref || v.reltags.type))
                  popup += " <i>" + 
                    $.trim((v.reltags.type ? htmlentities(v.reltags.type)+" " : "") +
                            (v.reltags.ref ?  htmlentities(v.reltags.ref)+" " : "") +
                            (v.reltags.name ? htmlentities(v.reltags.name)+" " : "")) +
                    "</i>";
                if (v["role"]) 
                  popup += " as <i>"+htmlentities(v["role"])+"</i>";
                popup += "</li>";
              });
              popup += "</ul>";
            }
            if (feature.properties && feature.properties.meta && !$.isEmptyObject(feature.properties.meta)) {
              popup += '<h3>Meta:</h3><ul class="plain">';
              $.each(feature.properties.meta, function (k,v) {
                k = htmlentities(k);
                v = htmlentities(v);
                if (k == "user")
                  v = '<a href="//www.openstreetmap.org/user/'+encodeURIComponent(v)+'" target="_blank">'+v+'</a>';
                if (k == "changeset")
                  v = '<a href="//www.openstreetmap.org/changeset/'+encodeURIComponent(v)+'" target="_blank">'+v+'</a>';
                popup += "<li>"+k+"="+v+"</li>";
              });
              popup += "</ul>";
            }
            if (feature.geometry.type == "Point")
              popup += "<h3>Coordinates:</h3><p>"+feature.geometry.coordinates[1]+" / "+feature.geometry.coordinates[0]+" <small>(lat/lon)</small></p>";
            if ($.inArray(feature.geometry.type, ["LineString","Polygon","MultiPolygon"]) != -1) {
              if (feature.properties && feature.properties.tainted==true) {
                popup += "<p><strong>Attention: incomplete geometry (e.g. some nodes missing)</strong></p>";
              }
            }
            var latlng;
            if (typeof e.target.getLatLng == "function")
              latlng = e.target.getLatLng(); // node-ish features (circles, markers, icons, placeholders)
            else
              latlng = e.latlng; // all other (lines, polygons, multipolygons)
            var p = L.popup({maxHeight:600},this).setLatLng(latlng).setContent(popup);
            p.layer = layer;
            fire("onPopupReady", p);
          });
        },
      }});

setTimeout(function() {
      overpass.osmLayer.addData(data,function() {

      // save geojson and raw data
      geojson = overpass.osmLayer.getGeoJSON();
      overpass.geojson = geojson;
      overpass.data = data;

      // calc stats
      stats.geojson = {
        polys: 0,
        lines: 0,
        pois:  0
      };
      for (var i=0; i<geojson.features.length; i++)
        switch (geojson.features[i].geometry.type) {
          case "Polygon":
          case "MultiPolygon":
            stats.geojson.polys++;
            break;
          case "LineString":
          case "MultiLineString":
            stats.geojson.lines++;
            break;
          case "Point":
          case "MultiPoint":
            stats.geojson.pois++;
            break;
        }
      overpass.stats = stats;

      if (!shouldCacheOnly)
        fire("onGeoJsonReady");

      // print raw data
      fire("onProgress", "printing raw data");
setTimeout(function() {
      overpass.resultText = jqXHR.responseText;
      fire("onRawDataPresent");

      // todo: the following would profit from some unit testing
      // this is needed for auto-tab-switching: if there is only non map-visible data, show it directly
      if (geojson.features.length === 0) { // no visible data
        // switch only if there is some unplottable data in the returned json/xml.
        if ((data_mode == "json" && data.elements.length > 0) ||
            (data_mode == "xml" && $("osm",data).children().not("note,meta,bounds").length > 0)) {
          // check for "only areas returned"
          if ((data_mode == "json" && _.all(data.elements, {type:"area"})) ||
              (data_mode == "xml" && $("osm",data).children().not("note,meta,bounds,area").length == 0))
            empty_msg = "only areas returned";
          // check for "ids_only" or "tags" on nodes
          else if ((data_mode == "json" && _.some(data.elements, {type:"node"})) ||
                    (data_mode == "xml" && $("osm",data).children().filter("node").length > 0))
            empty_msg = "no coordinates returned";
          // check for "ids_only" or "tags" on ways
          else if ((data_mode == "json" && _.some(data.elements, {type:"way"}) && !_.some(_.filter(data.elements, {type:"way"}), "nodes")) ||
                    (data_mode == "xml" && $("osm",data).children().filter("way").length > 0 && $("osm",data).children().filter("way").children().filter("nd").length == 0))
            empty_msg = "no coordinates returned";
          // check for "ids_only" or "tags" on relations
          else if ((data_mode == "json" && _.some(data.elements, {type:"relation"}) && !_.some(_.filter(data.elements, {type:"relation"}), "members")) ||
                    (data_mode == "xml" && $("osm",data).children().filter("relation").length > 0 && $("osm",data).children().filter("relation").children().filter("member").length == 0))
            empty_msg = "no coordinates returned";
          else
            empty_msg = "no visible data";
        } else if(data_mode == "error") {
          empty_msg = "an error occured";
        } else if(data_mode == "unknown") {
          empty_msg = "unstructured data returned";
        } else {
          empty_msg = "received empty dataset";
        }
        // show why there is an empty map
        fire("onEmptyMap", empty_msg, data_mode);
      }

      // closing wait spinner
      fire("onDone");
},1); // end setTimeout
      });
},1); // end setTimeout
},1); // end setTimeout
},1); // end setTimeout
      });
    };
    if(cache && cache.hasOwnProperty(query)) {
      onSuccessCb.apply(this, cache[query]);
    } else {
      overpass.ajax_request = $.ajax(server+"interpreter"+additional_get_data, {
      type: 'POST',
      data: {data:query},
      headers: request_headers,
      success: onSuccessCb,
      error: function(jqXHR, textStatus, errorThrown) {
        if (textStatus == "abort")
          return; // ignore aborted queries.
        fire("onProgress", "error during ajax call");
        if (jqXHR.status == 400 || jqXHR.status == 504 || jqXHR.status == 429) { // todo: handle those in a separate routine
          // pass 400 Bad Request errors to the standard result parser, as this is most likely going to be a syntax error in the query.
          this.success(jqXHR.responseText, textStatus, jqXHR);
          return;
        }
        overpass.resultText = jqXHR.resultText;
        var errmsg = "";
        if (jqXHR.state() == "rejected")
          errmsg += "<p>Request rejected. (e.g. server not found, request blocked by browser addon, request redirected, internal server errors, etc.)</p>";
        if (textStatus == "parsererror")
          errmsg += "<p>Error while parsing the data (parsererror).</p>";
        else if (textStatus != "error" && textStatus != jqXHR.statusText)
          errmsg += "<p>Error-Code: "+textStatus+"</p>";
        if ((jqXHR.status != 0 && jqXHR.status != 200) || jqXHR.statusText != "OK") // note to me: jqXHR.status "should" give http status codes
          errmsg += "<p>Error-Code: "+jqXHR.statusText+" ("+jqXHR.status+")</p>";
        fire("onAjaxError", errmsg);
        // closing wait spinner
        fire("onDone");
      },
    }); // getJSON

    }
    
  }

  // == initializations ==
})(); // end create overpass object













