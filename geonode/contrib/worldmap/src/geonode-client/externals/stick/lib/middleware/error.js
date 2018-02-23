/**
 * @fileOverview Middleware to catch errors and generate simple error pages.
 *
 * By default, resource `stick/middleware/error.html` is used as page template.
 * This can be set through the `app.error.template` property. This is the complete
 * list of properties that influence the behaviour of this middleware:
 *
 *  * __template__ the error page template (_string_)
 *  * __message__ static error message to use instead of actual message (_string_)
 *  * __location__ whether to report any information about the code location of the error (_boolean_)
 *  * __stack__ whether to include a JavaScript stack trace (_boolean_)
 *  * __javaStack__ whether to include a Java stack trace (_boolean_)
 *  
 * @example
 * app.configure("error");
 * app.error.template = module.resolve("500.html");
 * app.error.location = true;
 */
var strings = require('ringo/utils/strings');
var engine = require('ringo/engine');
var log = require('ringo/logging').getLogger(module.id);
var {Buffer} = require('ringo/buffer');

/**
 * Stick middleware factory to display error messages and stack traces.
 * @param {Function} next the wrapped middleware chain
 * @param {Object} app the Stick Application object
 * @returns {Function} a JSGI middleware function
 */
exports.middleware = function error(next, app) {

    app.error = {
        template: module.resolve('error.html'),
        message: true,
        location: true,
        stack: true,
        javaStack: false
    };

    return function error(request) {
        try {
            return next(request);
        } catch (error if !error.retry && !error.notfound) {
            return handleError(request, error, app.error);
        }
    };
};

function handleError(request, error, config) {
    var title, body = new Buffer();
    if (config.location) {
        title = String(error);
        if (error.fileName && error.lineNumber) {
            body.write('<p>In file <b>')
                .write(error.fileName)
                .write('</b> at line <b>')
                .write(error.lineNumber)
                .writeln('</b>');
        }
    }
    if (config.message) {
        if (!title) {
            title = error.message ?
                    [error.name, error.message].join(": ") : "Server Error";
        }
        body.writeln.apply(body, engine.getErrors().map(function(e) {
            return e.toHtml();
        }));
    } else {
        title = "Server Error";
    }
    if (config.stack && config.location && error.stack) {
        body.write('<h3>Script Stack</h3><pre>')
                .write(error.stack)
                .write('</pre>');
    }
    if (config.javaStack && config.location && error.rhinoException) {
        var writer = new java.io.StringWriter();
        var printer = new java.io.PrintWriter(writer);
        error.rhinoException.printStackTrace(printer);
        body.write('<h3>Java Stack</h3><pre>')
                .write(strings.escapeHtml(writer.toString()))
                .write('</pre>');
    }
    log.error(error);
    var template = getResource(config.template);
    var html = template.content.replace(/\{\{\s*(\w+)\s*\}\}/g, function(match, group) {
        switch(group) {
            case "title":
                return strings.escapeHtml(title);
            case "body":
                return body;
            default:
                return "";
        }
    });
    return {
        status: 500,
        headers: {"Content-Type": "text/html"},
        body: [html]
    };
}