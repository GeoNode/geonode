/**
 * @fileoverview This module provides middleware for reading
 * cookies from the request.
 *
 */

/**
 * This middleware provides support for cookie access.
 *
 * @param {Function} next the wrapped middleware chain
 * @param {Object} app the Stick Application object
 * @returns {Function} a JSGI middleware function
 */
exports.middleware = function session(next, app) {

    return function (req) {

        /**
         * A cookies object for the current request.
         * @see servletRequest
         */
        Object.defineProperty(req, "cookies", {
            get: function() {
                if (!cookies) {
                    var cookies = new ScriptableMap();
                    var servletCookies = req.env.servletRequest.getCookies();
                    if (servletCookies) {
                        servletCookies.forEach(function(cookie) {
                            cookies[cookie.getName()] = cookie.getValue();
                        });
                    }
                }
                return cookies;
            }
        });
        return next(req);
    };
};
