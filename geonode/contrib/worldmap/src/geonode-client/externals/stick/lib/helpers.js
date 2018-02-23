/**
 * @fileOverview A collection of helper functions that makes
 * working with Stick middleware easier.
 */

var objects = require("ringo/utils/objects");
var {urlEncode} = require("ringo/utils/http");

/**
 * Resolve a module name or module object to a JSGI application.
 */
var resolveApp = exports.resolveApp = function(app) {
    var resolved = typeof app === "string" ? require(app) : app;
    if (typeof resolved !== "function") {
        if (resolved && typeof resolved.app === "function") {
            resolved = resolved.app;
        } else {
            throw new Error("Could not resolve app: " + app);
        }
    }
    return resolved;
};

// declared after resolveApp to solve cyclic dependency
var mount = require("./middleware/mount");

/**
 * Return a link to an action configured using the `route` middleware.
 *
 * The link's URL is generated from the bindings argument as described for
 * the [urlFor helper](#urlFor).
 *
 * @param {object|string} app the application to link to
 * @param {object} bindings an object containing the bindings for the target URL.
 * @param {string} text the link text.
 */
exports.linkTo = function(app, bindings, text) {
    var href = urlFor(app, bindings);
    text = text || href;
    return '<a href="' + href + '">' + text + '</a>';
};

/**
 * Return a URL for an action configured using the `mount` and `route` middlewares.
 *
 * The `app` argument specifies the Stick application to link to, either as reference
 * to the app itself or as module id of a module exporting the app as `app`.
 * The `bindings` argument contains information needed to determine the target
 * action within that application. Properties in the bindings argument are interpreted
 * as follows:
 *
 *  * The `action` property, if present, identifies the name of the action to link to.
 *    Action names are determined from the path arguments provided to the `route`
 *    middleware by removing all placeholders and the leading slash. For example,
 *    the name for an action routed with `/edit/:id` is "edit".
 *
 *  * Properties in the bindings object that have a placeholder with the same name in
 *    the target route are used to provide the value for this placeholder.
 *    For example, to URI path to an action in application `app` routed with "/edit/:id" with
 *    id `5` can be generated as follows:
 *
 *         urlFor(app, {action: "edit", id: 5})
 *
 *  * All other properties in the bindings object are set as query parameters in the
 *    generated URL. For example, if "index" is a route with no placeholders then calling
 *    `urlFor("index", {do: "search"})` will generate the URL "/?do=search".
 *
 * Note that the values for the current request are used as default values for `action`
 * and route placehoders, so if you want to use to a different action or placeholder value
 * you need to make that explicit.
 *
 * @param {object|string} app the application to link to
 * @param {object} bindings an object containing the bindings for the target URL.
 */
var urlFor = exports.urlFor = function(app, bindings) {
    bindings = bindings ? objects.clone(bindings) : {};

    if (!app) {
        throw new Error("app binding is missing");
    }
    app = resolveApp(app);

    var baseUri = app.base || mount.lookup(app) || "";
    if (app.route) {
        baseUri += app.route.reverse(bindings);
    }

    // add any bindings left over by route.reverse() to the query string
    var unbound = Object.keys(bindings);
    if (unbound.length) {
        baseUri += "?" + urlEncode(bindings);
    }

    return baseUri;
};

/**
 * Create a response that redirects the client to a different URL.
 * @param {string|object} app either the URL as string or an app
 *        to be passed to `urlFor`
 * @param {bindings} bindings to pass to `urlFor` if first argument is an app.
 * @returns {object} a JSGI response that will redirect the client to the
 *        specified target
 */
exports.redirectTo = function(app, bindings) {
    var target;
    if (typeof app === "function") {
        target = urlFor(app, bindings);
    } else if (typeof app === "string") {
        target = app;
    } else {
        throw new Error("redirectTo requires an argument of type string or object");
    }
    return {
        status: 303,
        headers: {Location: target},
        body: ["See other: " + target]
    };
};

