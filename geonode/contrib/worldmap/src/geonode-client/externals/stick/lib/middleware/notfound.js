/**
 * @fileOverview Middleware for simple Not-Found pages.
 *
 * By default, resource `stick/middleware/notfound.html` is used as page template.
 * This can be set through the `app.notfound.template` property.
 *
 *  * __template__ the notfound page template (_string_)
 *
 * @example
 * app.configure("notfound");
 * app.notfound.template = "templates/404.html";
 */

/**
 * Stick middleware for simple 404-Not-Found pages.
 * @param {Function} next the wrapped middleware chain
 * @param {Object} app the Stick Application object
 * @returns {Function} a JSGI middleware function
 */

var {escapeHtml} = require("ringo/utils/strings");

exports.middleware = function notfound(next, app) {

    app.notfound = {
        template: module.resolve('notfound.html')
    };

    return function notfound(request) {
        try {
            return next(request);
        } catch (e if e.notfound) {
            var template = getResource(app.notfound.template);
            var body = template.content.replace(/\{\{\s*(\w+)\s*\}\}/g, function(match, group) {
                switch(group) {
                    case "title":
                        return app.notfound.title || "Not Found";
                    case "body":
                        return app.notfound.body || "<p>The requested URL <b>"
                                + escapeHtml(request.scriptName) + escapeHtml(request.pathInfo)
                                + "</b> was not found on the server.</p>";
                    default:
                        return "";
                }
            });
            return {
                status: 404,
                headers: {"Content-Type": "text/html"},
                body: [body]
            };
        }
    };
};
