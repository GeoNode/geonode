// the autoloader injects scripts into the document dynamically
// only suitable for development/debug mode

var FS = require("fs");
var STATIC = require("ringo/middleware/static").middleware;

// TODO: unhack this
var path = FS.normal(FS.join(module.directory, "..", "build", "buildkit", "lib"));
require.paths.push(path);
var CONFIG = require("buildkit/config");
var MERGE = require("buildkit/merge");

// TODO: convert this to a real template
var template = '                                                            \n\
(function() {                                                               \n\
                                                                            \n\
    var jsfiles = [@paths@];                                                \n\
                                                                            \n\
    var scripts = document.getElementsByTagName("script");                  \n\
    var parts = scripts[scripts.length-1].src.split("/");                   \n\
    parts.pop();                                                            \n\
    var path = parts.join("/");                                             \n\
                                                                            \n\
    var pieces = new Array(jsfiles.length);                                 \n\
                                                                            \n\
    var src;                                                                \n\
                                                                            \n\
    for(var i=0; i<jsfiles.length; i++) {                                   \n\
        src = path + "/" + jsfiles[i];                                      \n\
        pieces[i] = "<script src=\'" + src + "\'></script>";                \n\
    }                                                                       \n\
    document.write(pieces.join(""));                                        \n\
})();                                                                       \n\
';

var libLoader = function(section, order) {
    var paths = [];
    order.forEach(function(path) {
        paths.push("'@" + section + "/" + path + "'");
    });
    var body = template.replace("@paths@", paths.join(",\n"));    
    return function(env) {
        return {
            status: 200,
            headers: {"Content-Type": "text/javascript"},
            body: [body]
        };
    };
};

var scriptLoader = function(root, script) {
    return function(env) {
        var path = FS.join(root, script);
        var body = FS.read(path);
        return {
            status : 200,
            headers : {
                "Last-Modified": FS.lastModified(path).toUTCString(),
                "Content-Type": "text/javascript",
                "Content-Length": body.length.toString(10)
            },
            body : [body]
        };
    };
};


var notFound = function() {
    throw {notfound: true};
};

var App = function(config) {
    
    var sections = CONFIG.parse(config);
    var group, root, order, urls = {};
    for (var section in sections) {
        group = sections[section];
        // make root relative to config
        root = FS.join(FS.directory(config), group.root[0]);
        group.root = [root];
        order = MERGE.order(group);
        // create lib loader
        urls["/" + section] = libLoader(section, order);
        // create static loader for all scripts in lib
        var app = STATIC(root)(notFound);
        urls["/@" + section] = app; 
    }
    return URLMap(urls);
    
};

exports.App = App;

var URLMap = function(map, options) {
    var options = options || { longestMatchFirst : true },
        mapping = [];
        
    for (var location in map) {
        var app = map[location],
            host = null,
            match;
        
        if (match = location.match(/^https?:\/\/(.*?)(\/.*)/)) {
            host = match[1];
            location = match[2];
        }
            
        if (location.charAt(0) != "/") {
            throw new Error("paths need to start with / (was: " + location + ")");
        }
        
        mapping.push([host, location.replace(/\/+$/,""), app]);
    }
    // if we want to match longest matches first, then sort
    if (options.longestMatchFirst) {
        mapping = mapping.sort(function(a, b) {
            return (b[1].length - a[1].length) || ((b[0]||"").length - (a[0]||"").length);
        });
    }
    
    return function(env, path) {
        path = (path || env.pathInfo).replace(/\/+$/,"");
        var hHost = env.host, sPort = env.port;

        for (var i = 0; i < mapping.length; i++) {
            var host = mapping[i][0], location = mapping[i][1], app = mapping[i][2];

            if ((host === hHost || (host === null)) &&
                (location === path.substring(0, location.length)) &&
                (path.charAt(location.length) === "" || path.charAt(location.length) === "/"))
            {
                env = Object.create(env); // make a shallow "copy", since we're modifying SCRIPT_NAME / PATH_INFO

                env.scriptName += location;
                env.pathInfo = path.substring(location.length);

                return app(env);
            }
        }

        throw {notfound: true};
    }
}
