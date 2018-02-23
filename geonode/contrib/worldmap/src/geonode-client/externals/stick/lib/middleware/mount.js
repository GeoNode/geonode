/**
 * @fileOverview This module provides middleware for mounting other applications
 * on a specific URI path or virtual host.
 *
 * Applying this middleware adds a `mount` method to the application. The mount
 * method takes a path or virtual host specification and an application as arguments.
 * If the spec is a string, it is interpreted as the URI path on which the app will be
 * mounted. If it is an object, it may contain `path` or `host` properties
 * that will be matched against the URI path and `Host` header of incoming requests.
 * _Note that virtual host based mounting has not been tested so far._
 *
 * Mounting one application within another causes the `scriptName` and `pathInfo`
 * properties in the request object to be adjusted so that the mounted application
 * receives the same pathInfo as if it was the main application. This means
 * that forward and reverse request routing will usually work as expected.
 *
 * This middleware maintains an index mapping applications to mount points which
 * can be accessed using the [lookup](#lookup) function. The [stick/helpers][helpers]
 * module provides higher level functions for this which include support for the
 * route middleware.
 *
 * @example
 * app.configure("mount");
 * app.mount("/wiki", module.resolve("vendor/ringowiki"));
 */

var {Headers} = require("ringo/utils/http");
var {resolveApp} = require("../helpers");
var strings = require("ringo/utils/strings");

/**
 * Middleware to mount other application on specific URI paths or virtual hosts.
 * @param {Function} next the wrapped middleware chain
 * @param {Object} app the Stick Application object
 * @returns {Function} a JSGI middleware function
 */
exports.middleware = function Mount(next, app) {

    var mounts = [];

    // define mount() method on application object
    app.mount = function(spec, target) {
        if (typeof spec === "string") {
            spec = {path: spec};
        } else if (!spec) {
            throw new Error("Missing spec");
        }
        if (spec.path) {
            // set up canonical path with trailing slash
            if (strings.endsWith(spec.path, "/")) {
                spec.canonicalPath = spec.path;
                spec.path = spec.path.slice(0, -1);
            } else {
                spec.canonicalPath = spec.path + "/";
            }
        }

        spec.host = spec.host ? String(spec.host) : null;
        var resolved = resolveApp(target);

        // add mount info to mounted app for reverse lookup
        if (!resolved.mountInfo) {
            resolved.mountInfo = [];
        }
        resolved.mountInfo.push({parent: app, path: spec.path, host: spec.host});

        mounts.push({
            match: function(req) {
                var host = req.headers.get("host") || "";
                var path = req.pathInfo || "/";

                return (!spec.host || (host && strings.endsWith(host, spec.host)))
                    && (!spec.path || path === spec.path
                                   || (path && strings.startsWith(path, spec.canonicalPath)));
            },
            path: spec.path,
            canonicalPath: spec.canonicalPath,
            app: resolved
        });
        mounts.sort(mostSpecificPathFirst);
    };

    /**
     * Sort the mounts array by the most specific mount path first. This means the mount path with
     * the most slashes in it will be searched first.
     *
     * @param m1 mount 1
     * @param m2 mount 2
     */
    function mostSpecificPathFirst(m1, m2) {
        var slash1 = (m1.path || '').match(/\//g);
        slash1 = slash1 == null ? 0 : slash1.length;
        var slash2 = (m2.path || '').match(/\//g);
        slash2 = slash2 == null ? 0 : slash2.length;
        return slash2 - slash1;
    }

    // return middleware function
    return function mount(req) {

        Headers(req.headers);
        for (var i = 0, length = mounts.length; i < length; i++) {
            var mount = mounts[i];
            if (mount.match(req)) {

                // if trailing slash is missing redirect to canonical path
                if (req.pathInfo === mount.path && req.method === "GET") {
                    var location = req.scriptName + mount.canonicalPath;
                    if (req.queryString) location += "?" + req.queryString;
                    return {
                        status: 303,
                        headers: {"Location": location},
                        body: ["See other: ", location]
                    }
                }

                // adjust scriptName and pathInfo
                if (mount.path) {
                    req.scriptName += mount.path;
                    req.pathInfo = req.pathInfo.slice(mount.path.length);
                }
                return mount.app(req);
            }
        }
        return next(req);
    };
};

/**
 * Return the URI path of a mounted application 
 * @param target a mounted JSGI application
 * @returns the URI path of the application, or ""
 */
exports.lookup = function(target) {
    var resolved = resolveApp(target);
    if (!Array.isArray(resolved.mountInfo)) {
        return "";
    }
    var mounts = resolved.mountInfo,
        seen = [resolved],
        path = "";

    outer:
    while (mounts) {
        for (var i = 0; i < mounts.length; i++) {
            var mount = mounts[i];
            // currently the only way to recognize a root application is by
            // absence of mount infos. We might want to introduce some root flag.
            if (mount.parent && seen.indexOf(mount.parent) === -1) {
                seen.push(mount.parent);
                path = (mount.path || "") + path;
                mounts = mount.parent.mountInfo;
                continue outer;
            }
        }
        mounts = null;
    }
    return path;
};
