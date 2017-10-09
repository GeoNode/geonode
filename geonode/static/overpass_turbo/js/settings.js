// Settings class
var Settings = function(namespace,version) {
  // == private members ==
  var prefix = namespace+"_";
  var ls = {setItem:function(n,v){this[n]=v;}, getItem:function(n){return this[n]!==undefined?this[n]:null;}}; try { localStorage.setItem(prefix+"test",123); localStorage.removeItem(prefix+"test"); ls = localStorage; } catch(e) {};
  var settings_version = version;
  var version = +ls.getItem(prefix+"version");
  var settings = {};
  var upgrade_callbacks = [];

  // == public methods ==
  this.define_setting = function(name,type,preset,version) {
    settings[name] = {"type":type,"preset":preset,"version":version};
  };
  this.define_upgrade_callback = function(version,fun) {
    upgrade_callbacks[version] = fun;
  };

  this.set = function(name,value) {
    if (value === undefined) // use preset if no value is given
      value = settings[name].preset;
    if(settings[name].type != "String") // stringify all non-string values.
      value = JSON.stringify(value);
    ls.setItem(prefix+name, value);
  };
  this.get = function(name) {
    // initialize new settings
    if (settings[name].version > version)
      this.set(name,undefined);
    // load the setting
    var value = ls.getItem(prefix+name);
    if (settings[name].type != "String") // parse all non-string values.
      value = JSON.parse(value);
    return value;
  };

  this.load = function() {
    // load all settings into the objects namespace
    for (var name in settings) {
      this[name] = this.get(name);
    }
    // version upgrade
    if (version == 0)
      this.first_time_visit = true;
    if (version < settings_version) {
      for (var v = version+1; v<=settings_version; v++) {
        if (typeof upgrade_callbacks[v] == "function")
          upgrade_callbacks[v](this);
      }
      version = settings_version;
      ls.setItem(prefix+"version",version);
    }
  };
  this.save = function() {
    // save all settings from the objects namespace
    for (var name in settings) {
      this.set(name,this[name]);
    }
  };
};
// examples
examples = {
  "Drinking Water":{"overpass":"/*\nThis is an example Overpass query.\nTry it out by pressing the Run button above!\nYou can find more examples with the Load tool.\n*/\nnode\n  [amenity=drinking_water]\n  ({{bbox}});\nout;"},
  "Cycle Network":{"overpass":"/*\nThis shows the cycleway and cycleroute network.\n*/\n\n[out:json];\n\n(\n  // get cycle route relatoins\n  relation[route=bicycle]({{bbox}})->.cr;\n  // get cycleways\n  way[highway=cycleway]({{bbox}});\n  way[highway=path][bicycle=designated]({{bbox}});\n);\n\nout body;\n>;\nout skel qt;"},
  "Where am I?":{"overpass":"/*\nThis lists all areas which include the map center point.\n*/\n[out:json];\nis_in({{center}});\nout;"},
  "Mountains in Area":{"overpass":"/*\nThis shows all mountains (peaks) in the Dolomites.\nYou may want to use the \"zoom onto data\" button. =>\n*/\n\n[out:json];\n\n// search the area of the Dolmites\narea\n  [place=region]\n  [\"region:type\"=\"mountain_area\"]\n  [\"name:en\"=\"Dolomites\"];\nout body;\n\n// get all peaks in the area\nnode\n  [natural=peak]\n  (area);\nout body qt;\n\n// additionally, show the outline of the area\nrelation\n  [place=region]\n  [\"region:type\"=\"mountain_area\"]\n  [\"name:en\"=\"Dolomites\"];\nout body;\n>;\nout skel qt;"},
  "Map Call":{"overpass":"/*\nThis is a simple map call.\nIt returns all data in the bounding box.\n*/\n[out:xml];\n(\n  node({{bbox}});\n  <;\n);\nout meta;"},
  "MapCSS styling": {"overpass": "/*\nThis example shows how the data can be styled.\nHere, some common amenities are displayed in \ndifferent colors.\n\nRead more: http://wiki.openstreetmap.org/wiki/Overpass_turbo/MapCSS\n*/\n[out:json];\n\n(\n  node[amenity]({{bbox}});\n  way[amenity]({{bbox}});\n  relation[amenity]({{bbox}});\n);\nout body;\n>;\nout skel qt;\n\n{{style: /* this is the MapCSS stylesheet */\nnode, area\n{ color:gray; fill-color:gray; }\n\nnode[amenity=drinking_water],\nnode[amenity=fountain]\n{ color:blue; fill-color:blue; }\n\nnode[amenity=place_of_worship],\narea[amenity=place_of_worship]\n{ color:grey; fill-color:grey; }\n\nnode[amenity=~/(restaurant|hotel|cafe)/],\narea[amenity=~/(restaurant|hotel|cafe)/]\n{ color:red; fill-color:red; }\n\nnode[amenity=parking],\narea[amenity=parking]\n{ color:yellow; fill-color:yellow; }\n\nnode[amenity=bench]\n{ color:brown; fill-color:brown; }\n\nnode[amenity=~/(kindergarten|school|university)/],\narea[amenity=~/(kindergarten|school|university)/]\n{ color:green; fill-color:green; }\n}}"},
};
examples_initial_example = "Drinking Water";

// global settings object
var settings = new Settings(
  configs.appname !== "overpass-turbo" ? configs.appname : "overpass-ide", // todo: use appname consistently
  32 // settings version number
);

// map coordinates
settings.define_setting("coords_lat","Float",configs.defaultMapView.lat,1);
settings.define_setting("coords_lon","Float",configs.defaultMapView.lon,1);
settings.define_setting("coords_zoom","Integer",configs.defaultMapView.zoom,1);
// saves
settings.define_setting("code","Object",examples[examples_initial_example],1);
settings.define_setting("saves","Object",examples,1);
// api server
settings.define_setting("server","String",configs.defaultServer,1);
// sharing options
settings.define_setting("share_compression","String","auto",1);
settings.define_setting("share_include_pos","Boolean",false,1);
// code editor & map view
settings.define_setting("use_rich_editor","Boolean",true,1);
settings.define_setting("tile_server","String",configs.defaultTiles,1);
settings.define_setting("enable_crosshairs","Boolean",false,1);
// export settings
settings.define_setting("export_image_scale","Boolean",true,1);
settings.define_setting("export_image_attribution","Boolean",true,1);
// CORS/ajax/etc. settings
settings.define_setting("force_simple_cors_request","Boolean",false,11);
// background opacity
settings.define_setting("background_opacity","Float",1.0,13);
// autorepair message on "no visible data"
settings.define_setting("no_autorepair","Boolean",false,16);
// resizable panels
settings.define_setting("editor_width","String","",17);
// UI language
settings.define_setting("ui_language","String","auto",19);
// disable poi-o-matic
settings.define_setting("disable_poiomatic","boolean",false,21);
// show data stats
settings.define_setting("show_data_stats","boolean",true,21);

//settings.define_setting(,,,);

// upgrade callbacks
settings.define_upgrade_callback(12, function(s) {
  // migrate code and saved examples to new mustache style syntax
  var migrate = function(code) {
    code.overpass = code.overpass.replace(/\(bbox\)/g,"({{bbox}})");
    code.overpass = code.overpass.replace(/<bbox-query\/>/g,"<bbox-query {{bbox}}/>");
    code.overpass = code.overpass.replace(/<coord-query\/>/g,"<coord-query {{center}}/>");
    return code;
  }
  s.code = migrate(s.code);
  for (var ex in s.saves) {
    s.saves[ex] = migrate(s.saves[ex]);
  }
  s.save();
});
settings.define_upgrade_callback(18, function(s) {
  // enable "Include current map state in shared links" by default
  s.share_include_pos = true;
  s.save();
});
settings.define_upgrade_callback(20, function(s) {
  // update "Mountains in Area" example
  s.saves["Mountains in Area"]=examples["Mountains in Area"];
  s.save();
});
settings.define_upgrade_callback(22, function(s) {
  // categorize saved queries
  for (var q in s.saves) {
    if (examples[q])
      s.saves[q].type = "example";
    else
      s.saves[q].type = "saved_query";
  }
  // define some templates
  s.saves["key"] = {
    type: "template",
    parameters: ["key"],
    overpass: "<!--\nthis query looks for nodes, ways and relations \nwith the given key.\n-->\n{{key=???}}\n<osm-script output=\"json\">\n  <union>\n    <query type=\"node\">\n      <has-kv k=\"{{key}}\"/>\n      <bbox-query {{bbox}}/>\n    </query>\n    <query type=\"way\">\n      <has-kv k=\"{{key}}\"/>\n      <bbox-query {{bbox}}/>\n    </query>\n    <query type=\"relation\">\n      <has-kv k=\"{{key}}\"/>\n      <bbox-query {{bbox}}/>\n    </query>\n  </union>\n  <print mode=\"body\"/>\n  <recurse type=\"down\"/>\n  <print mode=\"skeleton\"/>\n</osm-script>"
  };
  s.saves["key-type"] = {
    type: "template",
    parameters: ["key", "type"],
    overpass: "<!--\nthis query looks for nodes, ways or relations \nwith the given key.\n-->\n{{key=???}}\n{{type=???}}\n<osm-script output=\"json\">\n  <query type=\"{{type}}\">\n    <has-kv k=\"{{key}}\"/>\n    <bbox-query {{bbox}}/>\n  </query>\n  <print mode=\"body\"/>\n  <recurse type=\"down\"/>\n  <print mode=\"skeleton\"/>\n</osm-script>"
  };
  s.saves["key-value"] = {
    type: "template",
    parameters: ["key", "value"],
    overpass: "<!--\nthis query looks for nodes, ways and relations \nwith the given key/value combination.\n-->\n{{key=???}}\n{{value=???}}\n<osm-script output=\"json\">\n  <union>\n    <query type=\"node\">\n      <has-kv k=\"{{key}}\" v=\"{{value}}\"/>\n      <bbox-query {{bbox}}/>\n    </query>\n    <query type=\"way\">\n      <has-kv k=\"{{key}}\" v=\"{{value}}\"/>\n      <bbox-query {{bbox}}/>\n    </query>\n    <query type=\"relation\">\n      <has-kv k=\"{{key}}\" v=\"{{value}}\"/>\n      <bbox-query {{bbox}}/>\n    </query>\n  </union>\n  <print mode=\"body\"/>\n  <recurse type=\"down\"/>\n  <print mode=\"skeleton\"/>\n</osm-script>"
  };
  s.saves["key-value-type"] = {
    type: "template",
    parameters: ["key", "value", "type"],
    overpass: "<!--\nthis query looks for nodes, ways or relations \nwith the given key/value combination.\n-->\n{{key=???}}\n{{value=???}}\n{{type=???}}\n<osm-script output=\"json\">\n  <query type=\"{{type}}\">\n    <has-kv k=\"{{key}}\" v=\"{{value}}\"/>\n    <bbox-query {{bbox}}/>\n  </query>\n  <print mode=\"body\"/>\n  <recurse type=\"down\"/>\n  <print mode=\"skeleton\"/>\n</osm-script>"
  };
  s.save();
});
settings.define_upgrade_callback(23, function(s) {
  s.saves["type-id"] = {
    type: "template",
    parameters: ["type", "id"],
    overpass: "<!--\nthis query looks for a node, way or relation \nwith the given id.\n-->\n{{type=???}}\n{{id=???}}\n<osm-script output=\"json\">\n  <id-query type=\"{{type}}\" ref=\"{{id}}\"/>\n  <print mode=\"body\"/>\n  <recurse type=\"down\"/>\n  <print mode=\"skeleton\"/>\n</osm-script>"
  };
  s.save();
});
settings.define_upgrade_callback(24, function(s) {
  // categorize saved queries
  for (var q in s.saves) {
    if (!s.saves[q].type)
      s.saves[q].type = "saved_query";
  }
  s.save();
});
settings.define_upgrade_callback(25, function(s) {
  // upgrade template description text
  for (var q in s.saves) {
    if (s.saves[q].type == "template") {
      s.saves[q].overpass = s.saves[q].overpass.replace("<!--\nt","<!--\nT");
      s.saves[q].overpass = s.saves[q].overpass.replace("\n-->","\nChoose your region and hit the Run button above!\n-->");
    }
  }
  s.save();
});
settings.define_upgrade_callback(27, function(s) {
  // rename "List Areas" to "Where am I?"
  if (!s.saves["Where am I?"]) {
    s.saves["Where am I?"] = s.saves["List Areas"];
    delete s.saves["List Areas"];
  }
  // add mapcss example
  s.saves["MapCSS styling"] = {
    type: "example",
    overpass: examples["MapCSS styling"]
  };
  s.save();
});
settings.define_upgrade_callback(28, function(s) {
  // generalize URLs to not explicitly use http protocol
  s.server = s.server.replace(/^http:\/\//,"//");
  s.tile_server = s.tile_server.replace(/^http:\/\//,"//");
  s.save();
});
settings.define_upgrade_callback(29, function(s) {
  // convert templates to wizard-syntax
  _.each(s.saves, function(save, name) {
    if (save.type !== "template") return;
    switch (name) {
      case "key":
        save.wizard = "{{key}}=*";
      break;
      case "key-type":
        save.wizard = "{{key}}=* and type:{{type}}";
      break;
      case "key-value":
        save.wizard = "{{key}}={{value}}";
      break;
      case "key-value-type":
        save.wizard = "{{key}}={{value}} and type:{{type}}";
      break;
      case "type-id":
        save.wizard = "type:{{type}} and id:{{id}} global";
      break;
      default:
        return;
    }
    delete save.overpass;
  });
  s.save();
});

settings.define_upgrade_callback(30, function(s) {
  // add comments for templates
  var chooseAndRun = "\nChoose your region and hit the Run button above!";
  _.each(s.saves, function(save, name) {
    if (save.type !== "template") return;
    switch (name) {
      case "key":
        save.comment = "This query looks for nodes, ways and relations \nwith the given key.";
        save.comment += chooseAndRun;
      break;
      case "key-type":
        save.comment = "This query looks for nodes, ways or relations \nwith the given key.";
        save.comment += chooseAndRun;
      break;
      case "key-value":
        save.comment = "This query looks for nodes, ways and relations \nwith the given key/value combination.";
        save.comment += chooseAndRun;
      break;
      case "key-value-type":
        save.comment = "This query looks for nodes, ways or relations \nwith the given key/value combination.";
        save.comment += chooseAndRun;
      break;
      case "type-id":
        save.comment = "This query looks for a node, way or relation \nwith the given id.";
        save.comment += "\nTo execute, hit the Run button above!";
      break;
      default:
        return;
    }
    delete save.overpass;
  });
  s.save();
});

settings.define_upgrade_callback(31, function(s) {
  // rewrite examples in OverpassQL
  _.each(s.saves, function(save, name) {
    if (save.type !== "example") return;
    switch (name) {
      case "Drinking Water":
      case "Cycle Network":
      case "Mountains in Area":
      case "Map Call":
      case "Where am I?":
      case "MapCSS styling":
        save.overpass = examples[name].overpass;
      break;
      default:
        return;
    }
  });
  delete s.saves["Drinking Water (Overpass QL)"];
  s.save();
});

settings.define_upgrade_callback(32, function(s) {
  // fix typo in query definition
  s.saves["MapCSS styling"].overpass = s.saves["MapCSS styling"].overpass.replace("<;",">;");
  s.save();
});