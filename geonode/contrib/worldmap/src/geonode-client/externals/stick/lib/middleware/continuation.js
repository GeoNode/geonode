/**
 * @fileOverview Provide support for JavaScript 1.7 generator actions. 
 * 
 * This middleware supports two types of yield values from generators: 
 * Promises and JSGI response objects.
 *
 * If a generator action yields a promise, this middleware adds a listener to that
 * promise that will feed the value back to the generator once the promise is resolved.
 * If the promise resolves to an error, the error is thrown in the generator.
 *
 * For example, if `promise` is a promise, the `yield` statement will interrupt execution
 * of the action until the promise is resolved, at which point the generator is resumed
 * with the value of the promise being assigned to the `resolved` variable.
 *
 *     var resolved = yield promise;
 *
 * If a generator action yields a JSGI response, the response is sent to the client.
 * To be able to yield more than one response from the same generator, the generator
 * has to be associated with a continuation id and stored in the user's session.
 * This is done by calling `continuation.activate()` before yielding the first
 * response. The `activate()` method tells the middleware to store the generator
 * in the user's session and returns a contination id.
 *
 * For subsequent invocations of the generator, the continuation id has to be set as
 * query string parameter with name `_c`. When suspended generator is resumed,
 * the new request object is passed in as value for the last yield statement.
 *
 *     function continuation(request) {
 *         var c = app.continuation.activate();
 *         while(true) {
 *             request = yield response.html(linkTo(app, {_c: c}));
 *         }
 *     }
 *
 *
 * See <http://blog.ometer.com/2010/11/28/a-sequential-actor-like-api-for-server-side-javascript/>
 * for background.
 */

var {defer} = require("ringo/promise");
var {redirectTo} = require("../helpers");
var strings = require("ringo/utils/strings");

exports.middleware = function continuation(next, app) {

    app.continuation = {
        timeout: 30000,
        activate: function() {
            var req = app.request;
            req.env.continuation = strings.random(10);
            return req.env.continuation;
        }
    };

    return function(request) {

        var response, generator;

        var callbackId = request.queryParams && request.queryParams._c;
        if (callbackId) {
            request.continuation = callbackId;
            var continuations = request.session && request.session.data._continuations;
            var continuation = continuations && continuations[callbackId];
            if (continuation) {
                generator = continuation.fn;
                request.env.bindings = continuation.bindings
            }
        }

        if (generator && typeof generator.send === "function") {
            response = generator.send(request);
        } else {
            response = next(request);
        }

        // check if response is a generator
        if (response && typeof response.next === "function") {
            generator = response;
            response = response.next();
        }

        if (generator) {
            if (response && typeof response.then === "function") {
                // generator returned a promise
                var deferred = defer();
                var handlePromise = function(p) {
                    p.then(
                        function(value) {
                            try {
                                var v = generator.send(value);
                                if (v && typeof v.then === "function") {
                                    handlePromise(v);
                                } else {
                                    deferred.resolve(v);
                                }
                            } catch (error) {
                                deferred.resolve(error, true);
                            }
                        },
                        function(error) {
                            deferred.resolve(error, true);
                            generator.throw(error);
                        }
                    );
                };
                handlePromise(response);
                deferred.promise.timeout = app.continuation.timeout;
                return deferred.promise;
            } else if (request.env.continuation) {
                // generator returned a response, check if callback was registered
                // make sure required middleware is installed
                if (!request.session) {
                    throw new Error("Continuation callbacks require session middleware");
                }
                if (!Object.getOwnPropertyDescriptor(request, "queryParams")) {
                    throw new Error("Continuation callbacks require params middleware");
                }
                var data = request.session.data;
                data._continuations = data._continuations || {};
                data._continuations[request.env.continuation] = {
                    fn: generator,
                    bindings: request.env.bindings
                };
            }

        }
        return response;
    };
};