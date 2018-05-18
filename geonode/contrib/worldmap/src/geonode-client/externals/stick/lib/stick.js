/**
 * @fileOverview The `stick` module provides the `Application` class
 * which is the centerpiece of the Stick framework.
 *
 * A Stick Application
 * is a JSGI application which provides means to compose complex
 * applications out of modular middleware components.  
 *
 */

var helpers = require("./helpers");
var stickware = require("./middleware");

/**
 * The application object is a JSGI application that wraps a middleware chain.
 *
 * When invoked without arguments, the `Application` constructor returns
 * an application that wraps an `unhandled` middleware that throws an Error
 * when called. Use [configure][#Application.prototype.configure] to add
 * middleware modules to the application.
 *
 * When invoked with an argument, it is used as initial value for the
 * application's middleware chain. 
 *
 * @param {function} nested the nested application (optional)
 */
var Application = exports.Application = function Application() {

    var middleware = unhandled,
        environments = {},
        locals = new java.lang.ThreadLocal();

    function app(req) {
        var oldLocals = locals.get();
        try {
            locals.set({request: req, base: req.scriptName});
            return middleware(req);
        } finally {
            locals.set(oldLocals);
        }
    }

    /**
     * Apply one or more middleware factories to this Application. Middleware will
     * be wrapped around the existing middleware chain, starting with the rightmost
     * argument. For example, the following invocation of configure on a newly
     * created Application object:
     *
     *     app.configure("error", "route");
     *
     * will result in `error(route(unhandled()))` as middleware chain.
     * @name Application.prototype.configure
     * @param middleware... one or middleware factories. These can be
     * defined as module names, imported modules, or middleware factories.
     * For the middleware that is part of Stick it is sufficient to
     * use the last part of the module id. e.g. "error" or "route".
     */
    Object.defineProperty(app, "configure", {
        value: function() {
            // prepend to existing middleware chain
            var components = Array.slice(arguments);
            middleware = wrap(components, middleware);
            return app;
        }
    });

    /**
     * Returns an Application object that shares the middleware chain of the original application,
     * but can be configured to contain additional middleware that is not shared with the parent application.
     *
     * Repeated calls of the env method with the same argument return the same application object.
     *
     * @name Application.prototype.env
     * @param {string} name the environment name
     */
    Object.defineProperty(app, "env", {
        value: function(name) {
            if (!environments[name]) {
                environments[name] = Application(proxy);
            }
            return environments[name];
        }
    });

    /**
     * The request object associated with the current thread, or null.
     * @name Application.prototype.request
     * @type object
     */
    Object.defineProperty(app, "request", {
        get: function() {
            var loc = locals.get();
            return loc ? loc.request : null;
        }
    });

    /**
     * This application's base URI path as used by the current request,
     * or null if unknown.
     * @name Application.prototype.base
     * @type string
     */
    Object.defineProperty(app, "base", {
        get: function() {
            var loc = locals.get();
            return loc ? loc.base : null;
        }
    });

    // resolve middleware helper
    function resolve(middleware) {
        if (typeof middleware === "string") {
            var module = stickware[middleware] || require(middleware);
            middleware = module.middleware;
        } else if (Array.isArray(middleware)) {
            // allow a middleware item to be itself a list of middlewares
            middleware = middleware.reduceRight(function(inner, outer) {
                return compose(resolve(outer), resolve(inner));
            });
        }
        if (typeof middleware !== "function") {
            if (middleware && typeof middleware.middleware === "function") {
                middleware = middleware.middleware;
            } else {
                throw new Error("Could not resolve middleware: " + middleware);
            }
        }
        return middleware;
    }

    // wrap middleware helper
    function wrap(middleware, next) {
        next = next || unhandled;
        if (!Array.isArray(middleware)) {
            return compose(resolve(middleware), next);
        }
        return middleware.reduceRight(function(inner, outer) {
            return compose(resolve(outer), inner);
        }, next);
    }

    // return the result of calling outer(inner, app), do some error checking
    // and set up better toString() methods
    function compose(outer, inner) {
        var composed = outer(inner, app);
        if (typeof composed !== "function") {
            throw new Error("Expected function as middleware, got " + composed);
        }
        var functionToString = Function.prototype.toString;
        if (composed.toString === functionToString) {
            var name = composed.name || outer.name || "anonymous";
            var innerName = inner.toString === functionToString ?
                    inner.name || "anonymous" : String(inner);
            composed.toString = function() {
                return name + " > " + innerName;
            }
        }
        return composed;
    }

    function proxy(req) {
        return middleware(req)
    }

    proxy.toString = function() {
        return app.toString();
    };

    app.toString = function() {
        return middleware.toString();
    };

    // If we got an argument use it as initial app/middleware
    if (arguments.length) {
        middleware = helpers.resolveApp(arguments[0]);
    }

    return app;
};

/**
 * Unhandled request handler.
 */
function unhandled(req) {
    var error = new Error("Unhandled request");
    error.notfound = true;
    throw error;
}

unhandled.toString = function() {
    return "unhandled";
};
