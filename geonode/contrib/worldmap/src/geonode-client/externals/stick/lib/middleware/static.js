/**
 * @fileOverview Middleware for serving static resources.
 *
 * This installs a `static()` method in the application that accepts the following arguments:
 *
 *  * `base`: the base resource directory (required)
 *
 *  * `index`: the name of a file to serve if the path matches a directory (e.g.
 *    "index.html")
 *
 * You can call `static()` multiple times to register multiple resources to be served.
 */

var response = require("ringo/jsgi/response");
var {mimeType} = require("ringo/mime");

/**
 * Middleware for serving static resources.
 *
 * @param {Function} next the wrapped middleware chain
 * @param {Object} app the Stick Application object
 * @returns {Function} a JSGI middleware function
 */
exports.middleware = function static(next, app) {

    var resourceConfigs = [];

    app.static = function(base, index) {
        var baseRepository, indexDocument;
        if (typeof base === "string") {
            baseRepository = getRepository(base);
        } else if (base instanceof org.ringojs.repository.Repository) {
            baseRepository = base;
        } else {
            throw new Error ("base must be of type String or Repository");
        }
        baseRepository.setRoot();
        resourceConfigs.push({
            repository: baseRepository,
            index: index
        });
    };

    return function static(request) {
        for each (var config in resourceConfigs) {
            var path = request.pathInfo;
            if (config.index && path.charAt(path.length-1) === "/") {
                path += config.index;
            }
            if (path.length > 1) {
                var resource = config.repository.getResource(path);
                if (resource && resource.exists()) {
                    return response.static(resource, mimeType(path, "text/plain"));
                }
            }
        }
        return next(request);
    };
};
