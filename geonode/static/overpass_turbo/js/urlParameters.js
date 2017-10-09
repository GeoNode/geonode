// urlParameters module
if (typeof turbo === "undefined") turbo={};
turbo.urlParameters = function(param_str) {
  // defaults
  t = {
    has_query: false,
    query: undefined,
    has_coords: false,
    coords: undefined,
    has_zoom: false,
    zoom: undefined,
    run_query: false
  }

  // split parameter string to arguments
  function split(param_str) {
    var args = {};
    if (typeof param_str === "string" && param_str.length > 0) {
      var get = param_str.substring(1).split("&");
      for (var i=0; i<get.length; i++) {
        var kv = get[i].split("=");
        var key = decodeURIComponent(kv.shift().replace(/\+/g,"%20"));
        var val = (kv.length > 0) ?
          decodeURIComponent(kv.join("=").replace(/\+/g,"%20")) :
          true;
        args[key] = val;
      }
    }
    return args;
  }
  var args = split(param_str);

  // interpret arguments
  if (args.q) { // compressed query set in url
    t.query = lzw_decode(Base64.decode(args.q));
    t.has_query = true;
  }
  if (args.Q) { // uncompressed query set in url
    t.query = args.Q;
    t.has_query = true;
  }
  if (args.c) { // map center & zoom (compressed)
    var tmp = args.c.match(/([A-Za-z0-9\-_]+)([A-Za-z0-9\-_])/);
    var decode_coords = function(str) {
      var coords_cpr = Base64.decodeNum(str);
      var res = {};
      res.lat = coords_cpr % (180*100000) / 100000 - 90;
      res.lng = Math.floor(coords_cpr / (180*100000)) / 100000 - 180;
      return res;
    }
    t.coords = decode_coords(tmp[1]);
    t.has_coords = true;
    t.zoom = Base64.decodeNum(tmp[2]);
    t.has_zoom = true;
  }
  if (args.C) { // map center & zoom (uncompressed)
    var tmp = args.C.match(/(-?[\d.]+);(-?[\d.]+);(\d+)/);
    t.coords = {lat: +tmp[1], lng: +tmp[2]};
    t.has_coords = true;
    t.zoom = +tmp[3];
    t.has_zoom = true;
  }
  if (args.lat && args.lon) { // map center coords (ols style osm.org parameters)
    t.coords = {lat: +args.lat, lng: +args.lon};
    t.has_coords = true;
  }
  if (args.zoom) { // map zoom level (old style osm.org parameter)
    t.zoom = +args.zoom;
    t.has_zoom = true;
  }
  if (args.template) { // load a template
    var template = settings.saves[args.template];
    if (template && template.type == "template") {
      // build query
      var q = template.wizard;
      var params = template.parameters;
      for (var i=0; i<params.length; i++) {
        var param = params[i];
        var value = args[param];
        if (typeof value !== "string") value="???";
        function quotes(s) {
          if (s.match(/^[a-zA-Z0-9_]+$/) === null)
            return '"'+s.replace(/"/g,'\\"')+'"';
          return s;
        }
        q = q.replace("{{"+param+"}}",quotes(value));
      }
      args.w = q; // let the wizard do the work
      var wizard_comment = template.comment;
    } else {
      console.log("template not found: "+args.template);
    }
  }
  if (args.w) { // construct a query using the wizard
    var ffs = turbo.ffs();
    var query = ffs.construct_query(args.w, wizard_comment);
    if (query) {
      t.query = query;
      t.has_query = true;
    } else {
      console.log("invalid wizard syntax:\n  "+args.w);
    }
  }
  if (args.R !== undefined) { // indicates that the supplied query shall be executed immediately
    if (t.has_query) // only run if there is also a query to execute
      t.run_query = true;
  }

  return t;
};