/**
 * @fileOverview This module provides support for parsing multipart MIME messages
 * used for file uploads.
 *
 * This module behaves analogous and can be used in combination with the
 * [params][middleware/params] middleware.
 */

var {isFileUpload, parseFileUpload, BufferFactory} = require("ringo/utils/http");

/**
 * Middleware factory to enable support for parsing file uploads.
 * @param {Function} next the wrapped middleware chain
 * @param {Object} app the Stick Application object
 * @returns {Function} a JSGI middleware function
 */
exports.middleware = function upload(next, app) {

    app.upload = {
        impl: BufferFactory
    };

    return function upload(req) {

        var postParams, desc = Object.getOwnPropertyDescriptor(req, "postParams");

        /**
         * An object containing the parsed HTTP POST parameters sent with this request.
         * @name request.postParams
         */
        Object.defineProperty(req, "postParams", {
            get: function() {
                if (!postParams) {
                    var contentType = req.env.servletRequest.getContentType();
                    if ((req.method === "POST" || req.method === "PUT")
                            && isFileUpload(contentType)) {
                        postParams = {};
                        var encoding = req.env.servletRequest.getCharacterEncoding();
                        parseFileUpload(this, postParams, encoding);
                    } else if (desc) {
                        postParams = desc.get ? desc.get.apply(req) : desc.value;
                    }
                }
                return postParams;
            }, configurable: true
        });

        return next(req);
    };

};