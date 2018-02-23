/**
 * @fileOverview A scalable HTTP client that provides both synchronous and
 * asynchronous modes of operation.
 */

importPackage(org.eclipse.jetty.client);

var objects = require('ringo/utils/objects');
var {ByteString, Binary} = require('binary');
var {Stream, TextStream} = require('io');
var {Buffer} = require('ringo/buffer');
var {Decoder} = require('ringo/encoding');
var {getMimeParameter, Headers, urlEncode} = require('ringo/utils/http');
var base64 = require('ringo/base64');
var {Deferred} = require('ringo/promise');
var log = require('ringo/logging').getLogger(module.id);

export('request', 'post', 'get', 'del', 'put');

/**
 * Wrapper around jetty.http.HttpCookie.
 */
var Cookie = function(cookieStr) {

    Object.defineProperties(this, {
        /**
         * @returns {String} the cookie's name
         */
        name: {
            get: function() {
                return cookie.getName();
            }
        },
        /**
         * @returns {String} the cookie value
         */
        value: {
            get: function() {
                return cookie.getValue();
            }
        },
        /**
         * @returns {String} the cookie domain
         */
        domain: {
            get: function() {
                return cookie.getDomain();
            }
        },
        /**
         * @returns {String} the cookie path
         */
        path: {
            get: function() {
                return cookie.getPath();
            }
        }
    });

    /**
     * Parses the cookie string passed as argument
     * @param {String} cookieStr The cookie string as received from the remote server
     * @returns {Object} An object containing all key/value pairs of the cookiestr
     */
    var parse = function(cookieStr) {
        if (cookieStr != null) {
            var cookie = {};
            var m = Cookie.PATTERN.exec(cookieStr);
            if (m) {
                cookie.name = m[1].trim();
                cookie.value = m[2] ? m[2].trim() : "";
            }
            while ((m = Cookie.PATTERN.exec(cookieStr)) != null) {
                var key = m[1].trim();
                var value = m[2] ? m[2].trim() : "";
                cookie[key.toLowerCase()] = value;
            }
            return cookie;
        }
        return null;
    };

    var cookieData = parse(cookieStr);
    // FIXME FUTURE httpclient doesn't care about maxage or httponly (yet) so we don't either
    var cookie = null;
    if (cookieData.name && cookieData.value) {
        if (cookieData.domain) {
            if (cookieData.path) {
                cookie = new org.eclipse.jetty.http.HttpCookie(
                    cookieData.name,
                    cookieData.value,
                    cookieData.domain,
                    cookieData.path
                );
            } else {
                cookie = new org.eclipse.jetty.http.HttpCookie(
                    cookieData.name,
                    cookieData.value,
                    cookieData.domain
                );
            }
        } else {
            cookie = new org.eclipse.jetty.http.HttpCookie(cookieData.name, cookieData.value);
        }
    }

    return this;
};

/**
 * An instance of java.text.SimpleDateFormat used for both parsing
 * an "expires" string into a date and vice versa
 * @type java.text.SimpleDateFormat
 * @final
 */
Cookie.DATEFORMAT = new java.text.SimpleDateFormat("EEE, dd-MMM-yy HH:mm:ss z");

/**
 * A regular expression used for parsing cookie strings
 * @type RegExp
 * @final
 */
Cookie.PATTERN = /([^=;]+)=?([^;]*)(?:;\s*|$)/g;


/**
 * An Exchange encapsulates the Request and Response of an HTTP Exchange.
 * @constructor
 * @name Exchange
 */
var Exchange = function(url, options, callbacks) {
    if (!url) throw new Error('missing url argument');

    this.toString = function() {
        return "[ringo.httpclient.Exchange] " + url;
    };

    Object.defineProperties(this, {
        /**
         * The response status code
         * @name Exchange.prototype.status
         */
        status: {
            get: function() {
                return exchange.getResponseStatus();
            }, enumerable: true
        },
        /**
         * The response content type
         * @name Exchange.prototype.contentType
         */
        contentType: {
            get: function() {
                return responseHeaders.get('Content-Type');
            }, enumerable: true
        },
        /**
         * The response body as String
         * @name Exchange.prototype.content
         */
        content: {
            get: function() {
                return exchange.getResponseContent();
            }, enumerable: true
        },
        /**
         * The response body as ByteString
         * @name Exchange.prototype.contentBytes
         */
        contentBytes: {
            get: function() {
                var bytes = exchange.getResponseContentBytes();
                return bytes ? ByteString.wrap(bytes) : new ByteString();
            }, enumerable: true
        },
        /**
         * @name Exchange.prototype.contentChunk
         */
        contentChunk: {
            get: function() {
                return exchange.getRequestContentChunk();
            }, enumerable: true
        },
        /**
         * The Jetty ContentExchange object
         * @see http://download.eclipse.org/jetty/7.0.2.v20100331/apidocs/org/eclipse/jetty/client/ContentExchange.html
         * @name Exchange.prototype.contentExchange
         */
        contentExchange: {
            get: function() {
                return exchange;
            }, enumerable: true
        },
        /**
         * The response headers
         * @name Exchange.prototype.headers
         */
        headers: {
            get: function() {
                return responseHeaders;
            }, enumerable: true
        },
        /**
         * The cookies set by the server
         * @name Exchange.prototype.cookies
         */
        cookies: {
            get: function() {
                var cookies = {};
                var cookieHeaders = responseHeaders.get("Set-Cookie");
                cookieHeaders = cookieHeaders ? cookieHeaders.split("\n") : [];
                for each (var header in cookieHeaders) {
                    var cookie = new Cookie(header);
                    cookies[cookie.name] = cookie;
                }
                return cookies;
            }, enumerable: true
        },
        /**
         * The response encoding
         * @name Exchange.prototype.encoding
         */
        encoding: {
            // NOTE HttpExchange._encoding knows about this but is protected
            get: function() {
                return getMimeParameter(this.contentType, "charset") || 'utf-8';
            }, enumerable: true
        },
        /**
         * True if the request has completed, false otherwise
         * @name Exchange.prototype.done
         */
        done: {
            get: function() {
                return exchange.isDone();
            }, enumerable: true
        },
        /**
         * Waits for the request to complete and returns the Exchange object itself.
         * This method returns immediately if the request has already completed.
         * Otherwise, it will block the current thread until completion.
         * @returns the Exchange object
         * @name Exchange.prototype.wait
         */
        wait: {
            value: function() {
                exchange.waitForDone();
                return this;
            }, enumerable: true
        }
    });

    var getStatusMessage = function(status) {
        var message;
        try {
            var code = org.eclipse.jetty.http.HttpStatus.getCode(status);
            message = code && code.getMessage();
        } catch (error) {
             // ignore
        }
        return message || "Unknown status code (" + status + ")";
    };

    /**
    * Constructor
    */

    var self = this;
    var responseHeaders = new Headers();
    var decoder;
    var exchange = new JavaAdapter(ContentExchange, {
        onResponseComplete: function() {
            try {
                this.super$onResponseComplete();
                var content = options.binary ? self.contentBytes : self.content;
                if (typeof(callbacks.complete) === 'function') {
                    callbacks.complete(content, self.status, self.contentType, self);
                }
                // This callback will only see a redirect status if the max number
                // of redirects handled by the RedirectListener are reached or
                // the client was instantianted with followRedirects = false.
                if (self.status >= 200 && self.status < 400) {
                    if (typeof(callbacks.success) === 'function') {
                        callbacks.success(content, self.status, self.contentType, self);
                    }
                } else if (typeof(callbacks.error) === 'function') {
                    var message = getStatusMessage(self.status);
                    callbacks.error(message, self.status, self);
                }
            } finally {
                if (options.async) {
                    global.exitAsyncTask();
                }
            }
            return;
        },
        onResponseContent: function(content) {
            if (typeof(callbacks.part) === 'function') {
                if (options.binary) {
                    var bytes = ByteString.wrap(content.asArray());
                    callbacks.part(bytes, self.status, self.contentType, self);
                } else {
                    decoder = decoder || new Decoder(self.encoding);
                    bytes = content.array();
                    if (bytes == null) {
                        decoder.decode(content.asArray(), 0, content.length());
                    } else {
                        decoder.decode(bytes, content.getIndex(), content.putIndex());
                    }
                    callbacks.part(decoder.toString(), self.status, self.contentType, self);
                    decoder.clear();
                }
            } else {
                this.super$onResponseContent(content);
            }
            return;
        },
        onResponseHeader: function(key, value) {
            this.super$onResponseHeader(key, value);
            responseHeaders.add(String(key), String(value));
            return;
        },
        onConnectionFailed: function(exception) {
            try {
                this.super$onConnectionFailed(exception);
                if (typeof(callbacks.error) === 'function') {
                    var message = exception.getMessage() || exception.toString();
                    callbacks.error(message, 0, self);
                }
            } finally {
                if (options.async) {
                    global.exitAsyncTask();
                }
            }
            return;
        },
        onException: function(exception) {
            try {
                this.super$onException(exception);
                if (typeof(callbacks.error) === 'function') {
                    var message = exception.getMessage() || exception.toString();
                    callbacks.error(message, 0, self);
                }
            } finally {
                if (options.async) {
                    global.exitAsyncTask();
                }
            }
            return;
        },
        onExpire: function() {
            try {
                this.super$onExpire();
                if (typeof(callbacks.error) === 'function') {
                    callbacks.error('Request expired', 0, self);
                }
            } finally {
                if (options.async) {
                    global.exitAsyncTask();
                }
            }
            return;
        },
    });

    exchange.setMethod(options.method);

    // deal with username:password in url
    var urlObj = new java.net.URL(url);
    var userInfo = urlObj.getUserInfo();
    if (userInfo) {
        // exchange.setURL does not take username:password in URL
        url = url.replace(userInfo + "@", "");
        var [username, password] = userInfo.split(":");
        options.username = options.username || username;
        options.password = options.password || password;
    }

    if (typeof(options.username) === 'string' && typeof(options.password) === 'string') {
        var authKey = base64.encode(options.username + ':' + options.password);
        var authHeaderValue = "Basic " + authKey;
        exchange.addRequestHeader("Authorization", authHeaderValue);
    }

    for (var headerKey in options.headers) {
        exchange.addRequestHeader(headerKey, options.headers[headerKey]);
    }

    // set content
    var content = options.data;

    if (options.method === 'POST' || options.method === 'PUT') {
        var {ByteArrayBuffer} = org.eclipse.jetty.io;
        if (content instanceof Binary) {
            exchange.setRequestContent(new ByteArrayBuffer(content));
        } else {
            if (content instanceof Stream || content instanceof java.io.InputStream) {
                exchange.setRequestContentSource(content);
            } else {
                if (content instanceof TextStream) {
                    // FIXME this relies on TextStream not being instanceof Stream
                    content = content.read();
                } else if (content instanceof Object) {
                    content = urlEncode(content);
                }
                if (typeof(content) === 'string') {
                    var charset = getMimeParameter(options.contentType, 'charset') || 'utf-8';
                    exchange.setRequestContent(new ByteArrayBuffer(content, charset));
                }
            }
        }
        exchange.setRequestContentType(options.contentType);
    } else {
        if (content instanceof Object) {
            content = urlEncode(content);
        }
        if (typeof(content) === 'string' && content.length) {
            url += "?" + content;
        }
    }
    exchange.setURL(url);
    // FIXME we could add a RedirectListener right here to auto-handle redirects

    return this;
};

/**
 * Defaults for options passable to to request()
 */
var defaultOptions = function(options) {
    var defaultValues = {
        // exchange
        data: {},
        headers: {},
        method: 'GET',
        username: undefined,
        password: undefined,
        // client
        async: false,
        cache: true,
        binary: false
    };
    var opts = options ? objects.merge(options, defaultValues) : defaultValues;
    Headers(opts.headers);
    opts.contentType = opts.contentType
            || opts.headers.get('Content-Type')
            || 'application/x-www-form-urlencoded;charset=utf-8';
    return opts;
};

/**
 * Of the 4 arguments to get/post all but the first (url) are optional.
 * This fn puts the right arguments - depending on their type - into the options object
 * which can be used to call request()
 * @param {Array} Arguments Array
 * @returns {Object<{url, data, success, error}>} Object holding attributes for call to request()
 */
var extractOptionalArguments = function(args) {

    var types = [];
    for each (var arg in args) {
        types.push(typeof(arg));
    }

    if (types[0] != 'string') {
        throw new Error('first argument (url) must be string');
    }

    if (args.length == 1) {
        return {
            url: args[0]
        };

    } else if (args.length == 2) {
        if (types[1] == 'function') {
            return {
                url: args[0],
                success: args[1]
            };
        } else {
            return {
                url: args[0],
                data: args[1]
            };
        }
        throw new Error('two argument form must be (url, success) or (url, data)');
    } else if (args.length == 3) {
        if (types[1] == 'function' && types[2] == 'function') {
            return {
                url: args[0],
                success: args[1],
                error: args[2]
            };
        } else if (types[1] == 'object' && types[2] == 'function') {
            return {
                url: args[0],
                data: args[1],
                success: args[2]
            };
        } else {
            throw new Error('three argument form must be (url, success, error) or (url, data, success)');
        }
    }
    throw new Error('unknown arguments');
};

/**
 * A HttpClient which can be used for multiple requests.
 *
 * Use this Client instead of the convenience methods if you do lots
 * of requests (especially if they go to the same hosts)
 * or if you want cookies to be preserved between multiple requests.

 * @param {Number} timeout The connection timeout
 * @param {Boolean} followRedirects If true then redirects (301, 302) are followed
 * @constructor
 */
var Client = function(timeout, followRedirects) {

    this.get = function(url, data, success, error) {
        if (arguments.length < 4) {
            var {url, data, success, error} = extractOptionalArguments(arguments);
        }
        return this.request({
            method: 'GET',
            url: url,
            data: data,
            success: success,
            error: error,
            async: typeof success === 'function'
        });
    };

    this.post = function(url, data, success, error) {
        if (arguments.length < 4) {
            var {url, data, success, error} = extractOptionalArguments(arguments);
        }
        return this.request({
            method: 'POST',
            url: url,
            data: data,
            success: success,
            error: error,
            async: typeof success === 'function'
        });
    };

    this.del = function(url, data, success, error) {
        if (arguments.length < 4) {
            var {url, data, success, error} = extractOptionalArguments(arguments);
        }
        return this.request({
            method: 'DELETE',
            url: url,
            data: data,
            success: success,
            error: error,
            async: typeof success === 'function'
        });
    };

    this.put = function(url, data, success, error) {
        if (arguments.length < 4) {
            var {url, data, success, error} = extractOptionalArguments(arguments);
        }
        return this.request({
            method: 'PUT',
            url: url,
            data: data,
            success: success,
            error: error,
            async: typeof success === 'function'
        });
    };

    this.request = function(options) {
        var opts = defaultOptions(options);
        if (opts.promise) {
            var deferred = new Deferred();
            opts.success = function() {deferred.resolve(arguments[3])};
            opts.error = function() {deferred.resolve(arguments[2], true)};
            opts.async = true;
        }
        var exchange = new Exchange(opts.url, {
            method: opts.method,
            data: opts.data,
            headers: opts.headers,
            username: opts.username,
            password: opts.password,
            contentType: opts.contentType,
            binary: opts.binary,
            async: opts.async
        }, {
            success: opts.success,
            complete: opts.complete,
            error: opts.error,
            part: opts.part
        });
        if (typeof(opts.beforeSend) === 'function') {
            opts.beforeSend(exchange);
        }
        try {
            client.send(exchange.contentExchange);
            if (opts.async) {
                global.enterAsyncTask();
            } else {
                exchange.contentExchange.waitForDone();
            }
        } catch (e) { // probably java.net.ConnectException
            if (typeof(opts.error) === 'function') {
                opts.error(e, 0, exchange);
            }
        }
        return opts.promise ? deferred.promise : exchange;
    };

    var client = new HttpClient();
    if (typeof timeout == "number") {
        if (timeout <= 0) {
            // Disable timeout if zero or negative
            timeout = java.lang.Long.MAX_VALUE;
        }
        client.setTimeout(timeout);
    }

    if (followRedirects !== false) {
        client.registerListener('org.eclipse.jetty.client.RedirectListener');
    }
    // client.setMaxRedirects(20); // jetty default = 20
    // client.setIdleTimeout(10000);
    // TODO proxy stuff
    //client.setProxy(Adress);
    //client.setProxyAuthentication(ProxyAuthorization);
    client.start();
    return this;
};

// avoid reinstantiating default client if module is reevaluated.
var defaultClient;

function getClient() {
    defaultClient = defaultClient || new Client();
    return defaultClient;
}

/**
 * Make a generic request.
 *
 * #### Generic request options
 *
 *  The `options` object may contain the following properties:
 *
 *  - `url`: the request URL
 *  - `method`: request method such as GET or POST
 *  - `data`: request data as string, object, or, for POST or PUT requests,
 *     Stream or Binary.
 *  - `headers`: request headers
 *  - `username`: username for HTTP authentication
 *  - `password`: password for HTTP authentication
 *  - `contentType`: the contentType
 *  - `async`: if true this method will return immedialtely , else it will block
 *     until the request is completed
 *  - `binary`: if true if content should be delivered as binary,
 *     else it will be decoded to string
 *  - `promise`: if true a promise that resolves to the request's Exchange
 *     object is returned instead of the Exchange object itself
 *
 *  #### Callbacks
 *
 *  The `options` object may also contain the following callback functions:
 *
 *  - `complete`: called when the request is completed
 *  - `success`: called when the request is completed successfully
 *  - `error`: called when the request is completed with an error
 *  - `part`: called when a part of the response is available
 *  - `beforeSend`: called with the Exchange object as argument before the request is sent
 *
 *  The following arguments are passed to the `complete`, `success` and `part` callbacks:
 *  1. `content`: the content as String or ByteString
 *  2. `status`: the HTTP status code
 *  3. `contentType`: the content type
 *  4. `exchange`: the exchange object
 *
 *  The following arguments are passed to the `error` callback:
 *  1. `message`: the error message. This is either the message from an exception thrown
 *     during request processing or an HTTP error message
 *  2. `status`: the HTTP status code. This is `0` if no response was received
 *  3. `exchange`: the exchange object
 *
 * @param {Object} options
 * @returns {Exchange} exchange object
 * @see #get
 * @see #post
 * @see #put
 * @see #del
 */
var request = function() {
    var client = getClient();
    return client.request.apply(client, arguments);
};

/**
 * Make a POST request. If a success callback is provided, the request is executed
 * asynchronously and the function returns immediately. Otherwise, the function
 * blocks until the request terminates.
 * @param {String} url the url to request
 * @param {Object|String|Binary|Stream} data request data, optional
 * @param {Function} success callback in case of successful status code, optional
 * @param {Function} error callback in case of any error - transmission or response, optional
 * @returns {Exchange} exchange object
 * @see #request
 */
var post = function() {
    var client = getClient();
    return client.post.apply(client, arguments);
};

/**
 * Make a GET request. If a success callback is provided, the request is executed
 * asynchronously and the function returns immediately. Otherwise, the function
 * blocks until the request terminates.
 * @param {String} url the url to request
 * @param {Object|String} data request data, optional
 * @param {Function} success callback in case of successful status code, optional
 * @param {Function} error callback in case of any error - transmission or response, optional
 * @returns {Exchange} exchange object
 * @see #request
 */
var get = function() {
    var client = getClient();
    return client.get.apply(client, arguments);
};

/**
 * Make a DELETE request. If a success callback is provided, the request is executed
 * asynchronously and the function returns immediately. Otherwise, the function
 * blocks until the request terminates.
 * @param {String} url the url to request
 * @param {Object|String} data request data, optional
 * @param {Function} success callback in case of successful status code, optional
 * @param {Function} error callback in case of any error - transmission or response, optional
 * @returns {Exchange} exchange object
 * @see #request
 */
var del = function() {
    var client = getClient();
    return client.del.apply(client, arguments);
};

/**
 * Make a PUT request. If a success callback is provided, the request is executed
 * asynchronously and the function returns immediately. Otherwise, the function
 * blocks until the request terminates.
 * @param {String} url the url to request
 * @param {Object|String|Binary|Stream} data request data, optional
 * @param {Function} success callback in case of successful status code, optional
 * @param {Function} error callback in case of any error - transmission or response, optional
 * @returns {Exchange} exchange object
 * @see #request
 */
var put = function() {
    var client = getClient();
    return client.put.apply(client, arguments);
};
