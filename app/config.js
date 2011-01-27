// map url patterns to exported JSGI app functions
var urls = [
    [(/^\/proxy/), require("./proxy").app]
];

var dir, pathMappings;

// debug mode loads unminified scripts
// assumes markup pulls in scripts under the path /servlet_name/script/
if (java.lang.System.getProperty("READYGXP_DEBUG")) {
    var fs = require("fs");
    dir = fs.join(module.directory, "..");
    var config = fs.normal(fs.join(dir, "buildjs.cfg"));
    urls.push(
        [(/^\/script(\/.*)/), require("./autoloader").App(config)]
    );    

    // path mappings for debug mode
    pathMappings = {
        "/externals/gxp/theme/": "/externals/gxp/src/theme/",
        "/theme/ux/colorpicker/": "/script/ux/colorpicker/",
        "/theme/ux/fileuploadfield/": "/script/ux/fileuploadfield/css/"
    };
}

exports.urls = urls;

// redirect requests without a trailing slash
// Jetty does this automatically for /servlet_name, Tomcat does not
function slash(config) {
    return function(app) {
        return function(request) {
            var response;
            var servletRequest = request.env.servletRequest;
            var pathInfo = servletRequest.getPathInfo();
            if (pathInfo === "/") {
                var uri = servletRequest.getRequestURI();
                if (uri.charAt(uri.length-1) !== "/") {
                    var location = servletRequest.getScheme() + "://" + 
                        servletRequest.getServerName() + ":" + servletRequest.getServerPort() + 
                        uri + "/";
                    return {
                        status: 301,
                        headers: {"Location": location},
                        body: []
                    };
                }
            }
            return app(request);
        };
    };
}

// custom middleware like static, but excludes url mappings from export.urls
var {Response} = require("ringo/webapp/response");
var {mimeType} = require("ringo/webapp/mime");
function almostStatic(config) {
    var base = getRepository(dir ? fs.join(dir, "app", "static") : module.resolve("static"));
    base.setRoot();
    return function(app) {
        return function(request) {
            var match = false;
            urls.forEach(function(url) {
                match = match || request.pathInfo.match(url[0]);
            });
            if (!match) {
                var path = request.pathInfo;
                if (path.charAt(path.length-1) === "/") {
                    path += "index.html";
                }
            
                if (pathMappings) {
                    for (var p in pathMappings) {
                        if (path.indexOf(p) == 0) {
                            path = path.replace(p, pathMappings[p]);
                            break;
                        }
                    }
                }

                if (path.length > 1) {
                    var resource = base.getResource(path);
                    if (resource && resource.exists()) {
                        return Response.static(resource, mimeType(path, "text/plain"));
                    }
                }
            }
            return app(request);
        }
    }
}

exports.middleware = [
    slash(),
    require("ringo/middleware/gzip").middleware,
    almostStatic(),
    require("ringo/middleware/error").middleware,
    require("ringo/middleware/notfound").middleware
];

exports.app = require("ringo/webapp").handleRequest;

exports.charset = "UTF-8";
exports.contentType = "text/html";
