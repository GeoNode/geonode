/**
 * @fileoverview The daemon control script invoked by the init script.
 *
 * This module interprets the first command line argument as module ID, load
 * the module and try to invoke the life cycle functions on it.
 *
 * For HTTP servers it is generally more convenient to directly use
 * `ringo/httpserver` which will create a new server instance and pass it to
 * as argument to the application life cycle functions.
 */

var system = require('system');
var log = require('ringo/logging').getLogger(module.id);

var app, appId;

export('init', 'start', 'stop', 'destroy');

/**
 * Called when the daemon instance is created.
 *
 * This function can be run with superuser id to perform privileged actions
 * before the daemon is started.
 */
function init() {
    log.info("init", system.args);
    // Remove our own script name from args
    system.args.shift();
    if (system.args.length) {
        appId = system.args[0];
        try {
            app = require(appId);
        } catch (error) {
            log.error("Error loading application module '" + appId + "'");
            log.error(error);
        }
    } else {
        log.error("No application module defined in command line arguments")
    }
    if (app && typeof app.init === "function") {
        app.init();
    }
}

/**
 * Called when the daemon instance is started.
 */
function start() {
    log.info("start");
    if (app && typeof app.start === "function") {
        app.start();
    }
}

/**
 * Called when the daemon is stopped.
 */
function stop() {
    log.info("stop");
    if (app && typeof app.stop === "function") {
        app.stop();
    }
}

/**
 * Called when the daemon is destroyed.
 */
function destroy() {
    log.info("destroy");
    if (app && typeof app.destroy === "function") {
        app.destroy();
    }
}

