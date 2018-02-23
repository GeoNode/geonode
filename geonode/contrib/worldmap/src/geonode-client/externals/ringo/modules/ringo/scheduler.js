/**
 * @fileoverview This module provides support for scheduling invocation of
 * functions.
 */

var engine = require("ringo/engine").getRhinoEngine();

/**
 * Executes a function after specified delay. The function will be called
 * in the thread of the local event loop. This means it will only run after
 * the currently executing code and other code running before it have
 * terminated.
 * @param {function} callback a function
 * @param {number} delay the delay in milliseconds
 * @param {...} [args] optional arguments to pass to the function
 * @returns {object} an id object useful for cancelling the scheduled
 * invocation
 * @see #clearTimeout()
 */
exports.setTimeout = function(callback, delay) {
    var args = Array.slice(arguments, 2);
    delay = parseInt(delay, 10) || 0;
    var worker = engine.getCurrentWorker();
    return worker.schedule(delay, this, callback, args);
};

/**
 * Cancel a timeout previuosly scheduled with [setTimeout()][#setTimeout].
 * @param {object} id the id object returned by setTimeout()
 * @see #setTimeout
 */
exports.clearTimeout = function(id) {
    try {
        var worker = engine.getCurrentWorker();
        worker.cancel(id);
    } catch (error) {
        // ignore
    }
};

/**
 * Calls a function repeatedly, with a fixed time delay between each call to
 * that function. The function will be called in the thread of the local event
 * loop. This means it will only run after the currently executing code and
 * other code running before it have terminated.
 * @param {function} callback a function
 * @param {number} delay the delay in milliseconds
 * @param {...} args optional arguments to pass to the function
 * @returns {object} an id object useful for cancelling the scheduled invocation
 * @see #clearInterval()
 */
exports.setInterval = function(callback, delay) {
    var args = Array.slice(arguments, 2);
    delay = Math.max(parseInt(delay, 10) || 0, 1);
    var worker = engine.getCurrentWorker();
    return worker.scheduleInterval(delay, this, callback, args);
};

/**
 * Cancel a timeout previuosly scheduled with [setInterval()][#setInterval].
 * @param {object} id the id object returned by setInterval()
 * @see #setInterval
 */
exports.clearInterval = function(id) {
    try {
        var worker = engine.getCurrentWorker();
        worker.cancel(id);
    } catch (error) {
        // ignore
    }
};
