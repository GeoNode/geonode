/**
 * @fileOverview This module provides response helper functions for composing
 * JSGI response objects.
 */

var {mimeType} = require('ringo/mime');

var charset = "utf-8";

/**
 * Get or set the character encoding used for text responses.
 *
 * If this function is called without argument, it returns the name of the
 * currently used character encoding. If called with an argument, it sets the
 * character encoding to the given charset.
 * @param {string} charset the encoding to use.
 * @returns {string} the current character encoding.
 */
exports.charset = function() {
    if (arguments.length) {
        charset = String(arguments[0]);
    }
    return charset;
}

/**
 * Create a JSGI response with content-type 'text/html' with the string
 * or binary arguments as response body.
 * @param {string} string... a variable number of strings to send as response body
 * @returns a JSGI response object of type text/html
 */
exports.html = function() {
    var contentType = "text/html"
    if (charset) contentType += "; charset=" + charset;
    return {
        status: 200,
        headers: {"Content-Type": contentType},
        body: Array.slice(arguments).map(String)
    }
};

/**
 * Create a JSGI response with content-type 'application/json' with the JSON
 * representation of the given object as response body.
 * @param {object} object the object whose JSON representation to return
 * @returns a JSGI response object of type application/json
 */
exports.json = function(object) {
    var contentType = "application/json"
    if (charset) contentType += "; charset=" + charset;
    return {
        status: 200,
        headers: {"Content-Type": contentType},
        body: [JSON.stringify(object)]
    };
};

/**
 * Create a JSGI response with content-type 'application/xml' with the given
 * XML document as response body.
 * @param {xml|string} xml an XML document
 * @returns a JSGI response object of type application/xml
 */
exports.xml = function(xml) {
    var contentType = "application/xml"
    if (charset) contentType += "; charset=" + charset;
    return {
        status: 200,
        headers: {"Content-Type": contentType},
        body: [typeof xml === 'xml' ? xml.toXMLString() : String(xml)]
    };
};

/**
 * A response representing a static resource.
 * @param {String|Resource} resource the resource to serve
 * @param {String} contentType optional MIME type. If not defined,
 *         the MIME type is detected from the file name extension.
 */
exports.static = function (resource, contentType) {
    if (typeof resource == 'string') {
        resource = getResource(resource);
    }
    if (!(resource instanceof org.ringojs.repository.Resource)) {
        throw Error("Wrong argument for static response: " + typeof(resource));
    }

    var input;
    return {
        status: 200,
        headers: {
            'Content-Type': contentType || mimeType(resource.name)
        },
        body: {
            digest: function() {
                return resource.lastModified().toString(36)
                    + resource.length.toString(36);
            },
            forEach: function(fn) {
                input = new Stream(resource.getInputStream());
                try {
                    input.forEach(fn);
                } finally {
                    input.close();
                }
            }
        }
    };
};

/**
 * Create a response with HTTP status code 303 that redirects the client
 * to a new location.
 * @param {String} location the new location
 */
exports.redirect = function (location) {
    return {
        status: 303,
        headers: {Location: location},
        body: ["See other: " + location]
    };
};

/**
 * Create a not-found response with HTTP status code 404.
 * @param {String} location the location that couldn't be found
 */
exports.notFound = function (location) {
    var contentType = "text/html"
    if (charset) contentType += "; charset=" + charset;
    var header = 'Not Found';
    var message = 'The requested URL ' + location + ' was not found on the server.';
    return {
        status: 404,
        headers: {'Content-Type': contentType},
        body: [ '<html><head><title>', header, '</title></head>',
                '<body><h1>', header, '</h1>',
                '<p>', message, '</p>',
                '</body></html>']
    };
};

/**
 * Create a error response with HTTP status code 500.
 * @param {String} message the message of response body
 */
exports.error = function (message) {
    var contentType = "text/html"
    if (charset) contentType += "; charset=" + charset;
    var header = "Server Error";
    message = message ? String(message) : "";
    return {
        status: 500,
        headers: {'Content-Type': contentType},
        body: [ '<html><head><title>', header, '</title></head>',
                '<body><h1>', header, '</h1>',
                '<p>', message, '</p>',
                '</body></html>']
    };
};

