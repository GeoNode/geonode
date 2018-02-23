/**
 * @fileoverview This module provides middleware for parsing
 * HTTP parameters from the query string and request body.
 *
 * It does not parse multipart MIME data such as file uploads which are handled
 * by the [upload][middleware/upload] module.
 */
var {isFileUpload, isUrlEncoded, parseFileUpload, parseParameters,
    mergeParameter, BufferFactory} = require("ringo/utils/http");
var objects = require("ringo/utils/objects");
var strings = require("ringo/utils/strings");

/**
 * Middleware for parsing HTTP parameters.
 * This module handles URL-endcoded form data transmitted in the query string
 * and request body as well as JSON encoded data in the request body.
 *
 * @param {Function} next the wrapped middleware chain
 * @param {Object} app the Stick Application object
 * @returns {Function} a JSGI middleware function
 */
exports.middleware = function params(next, app) {

    return function(req) {

        var params, queryParams, postParams;
        var desc = Object.getOwnPropertyDescriptor(req, "postParams");
        var servletRequest = req.env.servletRequest;

        /**
         * An object containing the parsed HTTP parameters sent with this request.
         * @name request.params
         */
        Object.defineProperty(req, "params", {
            get: function() {
                if (!params) {
                    params = objects.merge(this.postParams, this.queryParams);
                }
                return params;
            }, configurable: true
        });

        /**
         * An object containing the parsed HTTP query string parameters sent with this request.
         * @name request.queryParams
         */
        Object.defineProperty(req, "queryParams", {
            get: function() {
                if (!queryParams) {
                    queryParams = {};
                    var encoding = servletRequest.getCharacterEncoding() || "utf8";
                    parseParameters(this.queryString, queryParams, encoding);
                }
                return queryParams;
            }, configurable: true
        });

        /**
         * An object containing the parsed HTTP POST parameters sent with this request.
         * @name request.postParams
         */
        Object.defineProperty(req, "postParams", {
            get: function() {
                if (!postParams) {
                    var contentType = req.headers["content-type"];
                    if (req.method === "POST" || req.method === "PUT") {
                        var input;
                        var encoding = servletRequest.getCharacterEncoding() || "utf8";
                        if (isUrlEncoded(contentType)) {
                            postParams = {};
                            input = req.input.read();
                            var contentLength = parseInt(req.headers["content-length"]);
                            if (!input.length && contentLength > 0) {
                                // Entity body already consumed, ask servlet API for params
                                // See ringo issues #70 and #130
                                var map = servletRequest.getParameterMap();
                                for (var entry in Iterator(map.entrySet())) {
                                    var {key, value} = entry;
                                    // value is a java string array
                                    for each (var val in value) {
                                        mergeParameter(postParams, key, val);
                                    }
                                }
                            } else {
                                parseParameters(input, postParams, encoding);
                            }
                        } else if (strings.startsWith(contentType, "application/json")) {
                            input = req.input.read();
                            postParams = JSON.parse(input.decodeToString(encoding));
                        }
                    }
                    // query previous postParams property descriptor in case
                    // this is a file upload
                    if (!postParams && desc) {
                        postParams = desc.get ? desc.get.apply(req) : desc.value;
                    }
                }
                return postParams;
            }, configurable: true
        });

        return next(req);
    };

};