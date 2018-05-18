/**
 * @fileOverview Middleware for on-the-fly GZip compression of response bodies.
 *
 * By default only text content types are compressed. This can be controlled
 * using the `gzip.contentTypes` property:
 * @example
 * app.configure("gzip");
 * app.gzip.contentTypes = /^text|xml|json|javascript/;
 * 
 */
var {Binary, ByteArray, ByteString} = require('binary');
var {ResponseFilter, Headers} = require('ringo/utils/http');

var {ByteArrayOutputStream} = java.io;
var {GZIPOutputStream} = java.util.zip;

/**
 * JSGI middleware for GZIP compression.
 * @param {Function} next the wrapped middleware chain
 * @param {Object} app the Stick Application object
 * @returns {Function} a JSGI middleware function
 */
exports.middleware = function gzip(next, app) {

    // app.gzip.contentTypes is a regular expression that use used to determine
    // whether or not gzip encoding should be applied to a response
    app.gzip = {
        contentTypes: /^text|xml|json|javascript/
    };

    function canCompress(status, acceptEncoding, contentType, contentEncoding) {
        // Return true if content-type matches regex and other conditions are met
        return status == 200 && acceptEncoding && !contentEncoding
                && acceptEncoding.indexOf('gzip') > -1
                && contentType && contentType.match(app.gzip.contentTypes);
    }

    return function gzip(request) {
        var res = next(request),
            headers = Headers(res.headers);

        if (canCompress(res.status,
                request.headers["accept-encoding"],
                headers.get('Content-Type'),
                headers.get('Content-Encoding'))) {
            var bytes = new ByteArrayOutputStream(),
                gzip = new GZIPOutputStream(bytes);
            res.body = new ResponseFilter(res.body, function(part) {
                if (!(part instanceof Binary)) {
                    part = part.toByteString();
                }
                gzip.write(part);
                if (bytes.size() > 1024) {
                    var zipped = bytes.toByteArray();
                    bytes.reset();
                    return new ByteString(zipped);
                }
                return null;
            });
            res.body.close = function(fn) {
                gzip.close();
                fn(new ByteString(bytes.toByteArray()));
            };
            // headers.set('Content-Length', res.body.length)
            headers.set('Content-Encoding', 'gzip');
        }
        return res;
    };

};

