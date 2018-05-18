var assert = require("assert");
var {request, post, get, put, del} = require('ringo/httpclient');
var {Server} = require('ringo/httpserver');
var {html, json, notFound} = require('ringo/jsgi/response');
var {parseParameters, setCookie} = require('ringo/utils/http');
var {ByteArray} = require('binary');
var base64 = require('ringo/base64');

var server;
var host = "127.0.0.1";
var port = "8282";
var baseUri = "http://" + host + ":" + port + "/";

require('ringo/logging').setConfig(getResource('./httpclient_log4j.properties'));

/**
 * tests overwrite getResponse() to control the response they expect back
 */
var getResponse;

/**
 * setUp pre every test
 */
exports.setUp = function() {
    var handleRequest = function(req) {
        req.charset = 'utf8';
        req.pathInfo = decodeURI(req.pathInfo);
        return getResponse(req);
    };

    var config = {
       host: host,
       port: port
    };

    server = new Server(config);
    server.getDefaultContext().serveApplication(handleRequest);
    server.start();
    // test used to hang without this, but seems no longer the case
    // java.lang.Thread.currentThread().sleep(1000);
};

/**
 * tearDown after each test
 */
exports.tearDown = function() {
    server.stop();
    server.destroy();
    server = null;
};

/**
 * test that callbacks get called at all; all other
 * tests rely on that.
 */
exports.testCallbacksGetCalled = function() {
   getResponse = function(req) {
      return html('');
   };

   var successCalled, completeCalled, errorCalled;
   var exchange = request({
      url: baseUri,
      success: function() {
         successCalled = true;
      },
      complete: function() {
         completeCalled = true;
      },
      error: function() {
         errorCalled = true;
      }
   });
   assert.isTrue(successCalled);
   assert.isTrue(completeCalled);
   assert.isUndefined(errorCalled);
};

/**
 * test basic get
 */
exports.testBasic = function() {
   getResponse = function(req) {
      return html('<h1>This is the Response Text</h1>');
   };

   var errorCalled, myData;
   var exchange = request({
      url: baseUri,
      success: function(data, status, contentType, exchange) {
         myData = data;
      },
      error: function() {
         errorCalled = true;
      }
   });
   assert.isUndefined(errorCalled);
   assert.strictEqual(myData, '<h1>This is the Response Text</h1>');
};

/**
 * test user info in url
 */
exports.testUserInfo = function() {

    var log;
    getResponse = function(req) {
        log.push(req.headers["authorization"]);
        return html("response text");
    };

    // username and password in url
    log = [];
    request({url: "http://user:pass@" + host + ":" + port + "/"});
    assert.equal(log.length, 1, "user:pass - one request");
    assert.equal(typeof log[0], "string", "user:pass - one Authorization header");
    assert.equal(log[0].slice(0, 5), "Basic", "user:pass - Basic auth header");

    // username only in url, password in options
    log = [];
    request({url: "http://user@" + host + ":" + port + "/", password: "pass"});
    assert.equal(log.length, 1, "user - one request");
    assert.equal(typeof log[0], "string", "user - one Authorization header");
    assert.equal(log[0].slice(0, 5), "Basic", "user - Basic auth header");

    // username and password in url, options take precedence
    log = [];
    request({url: "http://user:pass@" + host + ":" + port + "/", username: "realuser", password: "realpass"});
    assert.equal(log.length, 1, "precedence - one request");
    assert.equal(typeof log[0], "string", "precedence - one Authorization header");
    assert.equal(log[0], "Basic " + base64.encode("realuser:realpass"), "precedence - Basic auth header");

}

/**
 * test servlet on request env (this is not httpclient specific, but uses same setUp tearDown)
 */
exports.testServlet = function() {

    var servlet;
    getResponse = function(req) {
        servlet = req.env.servlet;
        return html("servlet set");
    };

    var errorCalled, myData;
    var exchange = request({
        url: baseUri,
        success: function(data, status, contentType, exchange) {
            myData = data;
        },
        error: function() {
            errorCalled = true;
        }
    });
    assert.isUndefined(errorCalled);
    assert.strictEqual(myData, "servlet set");
    assert.ok(servlet instanceof javax.servlet.http.HttpServlet, "servlet instance");
};


/**
 * convenience wrappers
 */
exports.testConvenience = function() {
    getResponse = function(req) {
        var params = {};
        var input = req.method == "POST" ? req.input.read() : req.queryString;
        parseParameters(input, params);
        if (params.foo) {
            return html(req.method + ' with param');
        }
        return html(req.method);
    };
    var x = post(baseUri);
    assert.strictEqual(200, x.status);
    assert.strictEqual('POST', x.content);

    x = post(baseUri, {foo: 'bar'});
    assert.strictEqual(200, x.status);
    assert.strictEqual('POST with param', x.content);

    x = get(baseUri, {foo: 'bar'});
    assert.strictEqual(200, x.status);
    assert.strictEqual('GET with param', x.content);

    x = del(baseUri);
    assert.strictEqual(200, x.status);
    assert.strictEqual('DELETE', x.content);

    x = put(baseUri);
    assert.strictEqual(200, x.status);
    assert.strictEqual('PUT', x.content);
};


/**
 * GET, POST params
 */
exports.testParams = function() {
    getResponse = function(req) {
        var params = {};
        var input = req.method == "POST" ? req.input.read() : req.queryString;
        parseParameters(input, params);
        return json(params);
    };
    var data = {
        a: "fääßß",
        b: "fööööbääzz",
        c: "08083",
        d: "0x0004"
    };
    var getExchange = request({
        url: baseUri,
        method: 'GET',
        data: data
    });
    assert.strictEqual(200, getExchange.status);
    var receivedData = JSON.parse(getExchange.content);
    assert.deepEqual(data, receivedData);

    var postExchange = request({
        url: baseUri,
        method: 'POST',
        data: data
    });
    assert.strictEqual(200, postExchange.status);
    receivedData = JSON.parse(postExchange.content);
    assert.deepEqual(data, receivedData);
};

/**
 * Callbacks
 */
exports.testCallbacks = function() {
    getResponse = function(req) {
        if (req.pathInfo == '/notfound') {
            return notFound('error');
        } else if (req.pathInfo == '/success') {
            return json('success');
        } else if (req.pathInfo == '/redirect') {
            return {
                status: 302,
                headers: {Location: '/redirectlocation'},
                body: ["Found: " + '/redirectlocation']
            };
        } else if (req.pathInfo == '/redirectlocation') {
            return html('redirect success');
        }
    };
    var myStatus, successCalled, errorCalled, myMessage, myContentType, myData;
    // success shouldn't get called
    var getErrorExchange = request({
        url: baseUri + 'notfound',
        method: 'GET',
        complete: function(data, status, contentType, exchange) {
            myStatus = status;
        },
        success: function() {
            successCalled = true
        },
        error: function(message, status, exchange) {
            myMessage = message;
        }
    });
    assert.isUndefined(successCalled);
    assert.strictEqual(myStatus, 404);
    assert.strictEqual(getErrorExchange.status, 404);
    assert.strictEqual(myMessage, "Not Found");

    var getSuccessExchange = request({
        url: baseUri + 'success',
        method: 'GET',
        complete: function(data, status, contentType, exchange) {
            myStatus = status;
        },
        success: function(data, status, contentType, exchange) {
            myContentType = contentType;
        },
        error: function() {
            errorCalled = true;
        }
    });
    assert.strictEqual('application/json; charset=utf-8', myContentType);
    assert.strictEqual(200, myStatus);
    assert.isUndefined(errorCalled);

    var getRedirectExchange = request({
        url: baseUri + 'redirect',
        method: 'GET',
        complete: function(data, status, contentType, exchange) {
            myStatus = status;
            myData = data;
        },
        error: function(message) {
            errorCalled = true;
        }
    });
    assert.strictEqual(200, myStatus);
    assert.strictEqual('redirect success', myData);
    assert.isUndefined(errorCalled);
};

/**
 * Cookie set and read
 */
exports.testCookie = function() {
    var COOKIE_NAME = 'testcookie'
    var COOKIE_VALUE = 'cookie value with s p   a c es';

    getResponse = function(req) {
        var params = {};
        parseParameters(req.queryString, params);
        // set cookie
        var res = html('cookie set');
        res.headers['Set-Cookie'] = setCookie(COOKIE_NAME, params.cookievalue, 5);
        return res;
    };

    // receive cookie
    var myStatus, myExchange, errorCalled;
    request({
        url: baseUri,
        method: 'GET',
        data: {'cookievalue': COOKIE_VALUE},
        complete: function(data, status, contentType, exchange) {
            myStatus = status;
        },
        success: function(data, status, contentType, exchange) {
            myExchange = exchange;
        },
        error: function() {
            errorCalled = true;
        }
    });
    assert.isUndefined(errorCalled);
    assert.strictEqual(200, myStatus);
    assert.strictEqual(COOKIE_VALUE, myExchange.cookies[COOKIE_NAME].value);
};


/**
 * send stream and get the same stream back
 */
exports.testStreamRequest = function() {

    getResponse = function(req) {
        if (req.method == "POST") {
            var input;
            return {
                    status: 200,
                    headers: {
                        'Content-Type': 'image/png'
                    },
                    body: {
                        forEach: function(fn) {
                            var read, bufsize = 8192;
                            var buffer = new ByteArray(bufsize);
                            input = req.input;
                            while ((read = input.readInto(buffer)) > -1) {
                                buffer.length = read;
                                fn(buffer);
                                buffer.length = bufsize;
                            }
                        },
                        close: function() {
                            if (input) {
                                input.close();
                            }
                        }
                    }
                };

        }
    };

    var resource = getResource('./upload_test.png');
    var ByteArray = require('binary').ByteArray;
    var inputStream = resource.getInputStream();
    // small <1k file, just read it all in
    var size = resource.getLength();
    var inputByteArray = new ByteArray(size);
    inputStream.read(inputByteArray, 0, size);
    var sendInputStream = resource.getInputStream();
    var myExchange, myContentType, errorCalled;
    request({
        url: baseUri,
        method: 'POST',
        data: sendInputStream,
        error: function() {
            errorCalled = true;
        },
        complete: function(data, status, contentType, exchange) {
            myExchange = exchange;
            myContentType = contentType;
        }
    });
    assert.isUndefined(errorCalled);
    assert.isNotNull(myExchange);
    assert.strictEqual (inputByteArray.length, myExchange.contentBytes.length);
    assert.deepEqual (inputByteArray.toArray(), myExchange.contentBytes.toArray());
    assert.strictEqual('image/png', myContentType);
};

// start the test runner if we're called directly from command line
if (require.main == module.id) {
    system.exit(require("test").run(exports));
}
