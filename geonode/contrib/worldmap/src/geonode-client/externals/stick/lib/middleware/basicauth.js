/**
 * @fileOverview Basic Authentication middleware.
 *
 * To apply authentication to parts of your
 * website configure this middleware and call the app's basicauth method with
 * the URI path, user name, and SHA1 digest of the user's password as arguments for
 * each path you want to protect:
 *
 * @example
 * app.configure("basicauth");
 * app.basicauth('/protected/path', 'admin',
 *         '30B93F320076DE1304C34673F9F524F7EA7DB709');
 *
 */

var strings = require('ringo/utils/strings');
var base64 = require('ringo/base64');

/**
 *
 * @param {Function} next the wrapped middleware chain
 * @param {Object} app the Stick Application object
 * @returns {Function} a JSGI middleware function
 */
exports.middleware = function basicauth(next, app) {

    var config = {};

    app.basicauth = function(path, role, sha1) {
        config[path] = {};
        // strings.digest() uses upper-case hex encoding
        config[path][role] = String(sha1).toUpperCase();
    };

    return function basicauth(req) {
        // normalize multiple slashes in request path
        var path = (req.scriptName + req.pathInfo).replace(/\/+/g, '/');
        var toAuth;
        for (var realm in config) {
            if (path.indexOf(realm) == 0) {
                toAuth = config[realm];
                break;
            }
        }
        if (toAuth) {
            if (req.headers.authorization) { // Extract credentials from HTTP.
                var credentials = base64.decode(req.headers.authorization
                        .replace(/Basic /, '')).split(':');
                if (strings.digest(credentials[1], 'sha1') === toAuth[credentials[0]]) {
                    return next(req); // Authorization.
                }
            }
            var msg = '401 Unauthorized';
            return { // Access denied.
                status: 401,
                headers: {
                    'Content-Type': 'text/html',
                    'WWW-Authenticate': 'Basic realm="Secure Area"'
                },
                body: [
                    '<html><head><title>', msg, '</title></head>',
                    '<body><h1>', msg, '</h1>',
                    '</body></html>'
                ]
            };
        }
        return next(req);
    }
};
