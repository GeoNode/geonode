/**
 * @fileOverview Allows to work with deferred values that will be resolved in the future.
 */

export("Deferred", "PromiseList");

var NEW = 0;
var FULFILLED = 1;
var FAILED = 2;

/**
 * Creates an object representing a deferred value.
 * The deferred object has two properties: a [promise][#Promise]
 * object and a [resolve()][#Deferred.prototype.resolve] function.
 *
 * The promise object can be used to [register a callback](#Promise.prototype.then)
 * to be invoked when the promise is eventually resolved.
 *
 * The [resolve](#Deferred.prototype.resolve) function is used to resolve the
 * promise as either fulfilled or failed.
 *
 * @constructor
 * @example
 * // Example for an asynchronous JSGI response.
 * // The response is generated after a one second delay.
 * exports.asyncAction = function(request) {
 *   var response = new Deferred();
 *   setTimeout(function() {
 *       response.resolve({
 *           status: 200, headers: {}, body: ["Delayed"]
 *       });
 *   }, 1000);
 *   return response.promise;
 * }
 */
function Deferred() {
    var value;
    var listeners = [];
    var state = NEW;
    var lock = new java.lang.Object();

    /**
     * Resolve the promise.
     * @name Deferred.prototype.resolve
     * @param {Object} result the result or error value
     * @param {boolean} isError if true the promise is resolved as failed
     * @type function
     */
    var resolve = sync(function(result, isError) {
        if (state !== NEW) {
            throw new Error("Promise has already been resolved.");
        }
        value = result;
        state = isError ? FAILED : FULFILLED;
        listeners.forEach(notify);
        listeners = [];
        lock.notifyAll();
    }, lock);

    var notify = function(listener) {
        var isError = state === FAILED;
        var callback = isError ? listener.errback : listener.callback;
        if (!callback) {
            // if no callback defined we pass through the value
            listener.tail.resolve(value, isError);
        } else {
            try {
                listener.tail.resolve(callback(value), isError);
            } catch (error) {
                listener.tail.resolve(error, true);
            }
        }
    };

    /**
     * The promise object can be used to [register a callback](#Promise.prototype.then)
     * to be invoked when the promise is eventually resolved.
     * @name Deferred.prototype.promise
     */
    var promise = {
        /**
         * Register callback and errback functions to be invoked when
         * the promise is resolved.
         * @name Promise.prototype.then
         * @param {function} callback called if the promise is resolved as fulfilled
         * @param {function} errback called if the promise is resolved as failed
         * @return {Object} a new promise that resolves to the return value of the
         *     callback or errback when it is called.
         */
        then: sync(function(callback, errback) {
            if (typeof callback !== "function") {
                throw new Error("First argument to then() must be a function.");
            }
            var tail = new Deferred();
            var listener = {
                tail: tail,
                callback: callback,
                errback: errback
            };
            if (state === NEW) {
                listeners.push(listener);
            } else {
                notify(listener);
            }
            return tail.promise;
        }, lock),

        /**
         * Wait for the promise to be resolved.
         * @name Promise.prototype.wait
         * @param {Number} timeout optional time in milliseconds to wait for.
         *                 If timeout is undefined wait() blocks forever.
         * @return {Object} the value if the promise is resolved as fulfilled
         * @throws Object the error value if the promise is resolved as failed
         */
        wait: sync(function(timeout) {
            if (state === NEW) {
                if (typeof timeout === "undefined") {
                    lock.wait();
                } else {
                    lock.wait(timeout);
                }
            }
            if (state === FAILED) {
                throw value;
            } else {
                return value;
            }
        }, lock)
    };

    return {
        resolve: resolve,
        promise: promise
    };
}

/**
 * The PromiseList class allows to combine several promises into one.
 * It represents itself a promise that resolves to an array of objects,
 * each containing a `value` or `error` property with the value
 * or error of the corresponding promise argument.
 *
 * A PromiseList resolves successfully even if some or all of the partial
 * promises resolve to an error. It is the responsibility of the handler
 * function to check each individual promise result.
 *
 * @param {promise} promise... any number of promise arguments.
 * @constructor
 */
function PromiseList() {
    var promises = Array.slice(arguments);
    var count = new java.util.concurrent.atomic.AtomicInteger(promises.length);
    var results = [];
    var i = 0;
    var deferred = new Deferred();

    promises.forEach(function(promise) {
        if (typeof promise.then !== "function" && promise.promise) {
            promise = promise.promise;
        }
        var index = i++;
        promise.then(
            sync(function(value) {
                results[index] = {value: value};
                if (count.decrementAndGet() == 0) {
                    deferred.resolve(results);
                }
            }, count),
            sync(function(error) {
                results[index] = {error: error};
                if (count.decrementAndGet() == 0) {
                    deferred.resolve(results);
                }
            }, count)
        );
    });
    return deferred.promise;
}

/**
 * A promise object. This class is not exported, create a
 * [deferred object][#Deferred] to create a promise.
 * @name Promise
 */