/**
 * @fileOverview This module provides profiling middleware to measure
 * the application's runtime behaviour.
 *
 * Profiler data is written to the module's logger. You have to run the
 * application in interpreted mode (passing `-o -1` on the command line)
 * to get meaningful results.
 */

var engine = require('ringo/engine');
var Profiler = require('ringo/profiler').Profiler;
var Buffer = require('ringo/buffer').Buffer;
var log = require('ringo/logging').getLogger(module.id);

/**
 * A middleware factory that runs the nested app with a runtime profiler.
 *  
 * @param {Function} next the wrapped middleware chain
 * @param {Object} app the Stick Application object
 * @returns {Function} a JSGI middleware function
 */
exports.middleware = function profiler(next, app) {

    app.profiler = {
        // limit frames shown in the profiler
        maxFrames: 30
    };

    return function profiler(request) {
        if (engine.getOptimizationLevel() > -1) {
            // restart evaluation in interpreter mode. Shared modules
            // will still be optimized, so issue a warning
            log.error("The profiler needs to be run with --optlevel -1");
            /* if (typeof request.reset === "function") {
                request.reset();
            }
            engine.setOptimizationLevel(-1);
            throw {retry: true}; */
        }
        var profiler = new Profiler();
        profiler.attach();

        // get the response passing the request on to the middleware chain
        try {
            return next(request);
        } finally {
            log.info("\n" + profiler.formatResult(app.profiler.maxFrames));
        }
    }
};
