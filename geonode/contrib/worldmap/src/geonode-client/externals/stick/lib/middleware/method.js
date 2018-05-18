/**
 * @fileoverview JSGI middleware for HTTP method override.
 *
 * Since browsers
 * are not able to send HTTP requests with methods other than `GET`
 * and `POST`, this middleware allows the method of `POST` requests to be
 * overridden based on the value of a HTTP form parameter. The default
 * name for the override parameter is `_method`. This can be configured
 * through the `method.key` property.
 * @example
 * app.configure("method");
 * app.method.key = "__method"; 
 */

/**
 * JSGI middleware for HTTP method override.
 * @param {Function} next the wrapped middleware chain
 * @param {Object} app the Stick Application object
 * @returns {Function} a JSGI middleware function

 */
exports.middleware = function method(next, app) {

    app.method = {
        key: "_method"
    };

    return function method(req) {
        if (req.method === "POST") {
            if (!req.params) {
                throw new Error("method middleware requires params middleware");
            }
            var key = app.method.key;
            if (req.params[key]) {
                req.method = req.params[key].toUpperCase();
            }
        }
        return next(req);
    }
};