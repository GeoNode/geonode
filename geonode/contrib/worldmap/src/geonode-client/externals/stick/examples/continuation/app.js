
// see http://blog.ometer.com/2010/11/28/a-sequential-actor-like-api-for-server-side-javascript/

var {Application} = require("stick");
var {linkTo, redirectTo} = require("stick/helpers");
var {html} = require("ringo/jsgi/response");
var {defer, promises} = require("ringo/promise");
var {setTimeout} = require("ringo/scheduler");
var {request} = require("ringo/httpclient");

var app = exports.app = Application();
app.configure("error", "notfound", "session", "params", "continuation", "route");

// generator action that yields a promise and is resumed when the promise
// is resolved, yielding a JSGI response
app.get("/", function (req) {
    var deferred = defer();
    // resolve promise 2 seconds from now to "hello world"
    setTimeout(deferred.resolve, 2000, "hello world");
    // yield a promise
    var body = yield deferred.promise;
    // yield the actual response
    yield html(body);
});

// generator action that fetches 3 URLs in parallel, yields a promise for the
// requests and is resumed when all requests are finished, returning a JSGI
// response with the HTTP status codes
app.get("/http", function(req) {
    var results = yield promises(
        request({url: "http://www.orf.at", promise: true}),
        request({url: "http://localhost:8080/foo", promise: true}),
        request({url: "http://www.google.at/", promise: true}));
    yield html(results.map(function(res) {
        return res.error ? "Error: " + res.error.status :
                           "Success: " + res.value.status;
    }).join("<br/>"));
});

// same as index action above, but resolve to error
app.get("/error", function(req) {
    var deferred = defer();
    // resolve promise 2 seconds from now to an error
    setTimeout(deferred.resolve, 2000, "something went wrong", true);
    // yield a promise
    var body = yield deferred.promise;
    // yield the actual response
    yield html(body);
});

// an example for a user/jsgi continuation. The generator is stored
// in the user's session and yields a response each time the
// continuation middleware sees a request with the generator's id.
app.get("/counter", function(req) {
    var counter = 0;
    var c = app.continuation.activate();
    request = yield redirectTo(app, {_c: c});
    while (true) {
        req = yield html(
                "<h1>", counter, "</h1><p>",
                linkTo(app, {_c: c, inc: 1}, "++"), " ",
                linkTo(app, {_c: c, inc: -1}, "--"), "</p>");
        counter += (+req.queryParams.inc || 0);
    }
});

// This is a plain old promise based asynchronous action. Does not rely on
// continuation middleware, just here for reference and comparison.
app.get("/async", function(req) {
    var deferred = defer();
    setTimeout(deferred.resolve, 2000, html("delayed"));
    // return a promise
    return deferred.promise;    
});


// start server if run as main script
if (require.main === module) {
    require("ringo/httpserver").main(module.id);
}

