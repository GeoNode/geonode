var {Application} = require("stick");

var app = Application();
app.configure("notfound", "error", "static", "params", "mount");
app.static(module.resolve("static"), "index.html");
app.mount("/proxy", require("./root/proxy").app);

// debug mode loads unminified scripts
// assumes markup pulls in scripts under the path /servlet_name/script/
var pathMappings;
if (java.lang.System.getProperty("app.debug")) {
    var fs = require("fs");
    var config = fs.normal(fs.join(module.directory, "..", "buildjs.cfg"));
    app.mount("/script/", require("./autoloader").App(config));

    // path mappings for debug mode
    pathMappings = {
        "/externals/gxp/theme/": "/externals/gxp/src/theme/",
        "/theme/ux/colorpicker/": "/script/ux/colorpicker/",
        "/theme/ux/fileuploadfield/": "/script/ux/fileuploadfield/css/"
    };

    // proxy a remote geoserver on /geoserver by setting proxy.geoserver to remote URL
    // only recommended for debug mode
    var geoserver = java.lang.System.getProperty("app.proxy.geoserver");
    if (geoserver) {
        if (geoserver.charAt(geoserver.length-1) !== "/") {
            geoserver = geoserver + "/";
        }
        // debug specific proxy
        app.mount("/geoserver/", require("./root/proxy").pass({url: geoserver, preserveHost: true}));
    }
}

// Redirect requests for servlet name without a trailing slash.
// Jetty does this automatically for /servlet_name, Tomcat does not.
// Also rewrites requests to map directory structure for debug mode.
function rewrite(app) {
    return function(request) {
        var servletRequest = request.env.servletRequest;

        function redirect(location) {
            var location = servletRequest.getScheme() + "://" + 
                servletRequest.getServerName() + ":" + servletRequest.getServerPort() + 
                location;
            return {
                status: 301,
                headers: {"Location": location},
                body: []
            };
        }

        var uri = servletRequest.getRequestURI();
        var pathInfo = servletRequest.getPathInfo();
        if (pathInfo === "/") {
            if (uri.charAt(uri.length-1) !== "/") {
                return redirect(uri + "/");
            }
        }
        if (pathMappings) {
            for (var p in pathMappings) {
                if (uri.indexOf(p) === 0) {
                    return redirect(uri.replace(p, pathMappings[p]));
                }
            }
        }

        return app(request);
    };
}

exports.app = rewrite(app);

// main script to start application
if (require.main === module) {
    require("ringo/httpserver").main(module.id);
}