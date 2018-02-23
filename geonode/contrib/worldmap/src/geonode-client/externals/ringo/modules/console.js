/**
 * @fileOverview This module provides a familiar console object for
 * logging and debugging.
 */
var {TermWriter, BOLD, ONRED, ONYELLOW, RESET} = require("ringo/term");

var writer = new TermWriter(system.stderr);
var timers = {};
var {traceHelper, assertHelper} = org.ringojs.util.ScriptUtils;

function format() {
    var msg = arguments[0] ? String(arguments[0]) : "";
    var pattern = /%[sdifo]/;
    for (var i = 1; i < arguments.length; i++) {
        msg = pattern.test(msg)
                ? msg.replace(pattern, String(arguments[i]))
                : msg + " " + arguments[i];
    }
    return msg;
}

/**
 * Logs a message to the console.
 *
 * The first argument to log may be a string containing printf-like placeholders.
 * Otherwise, multipel arguments will be concatenated separated by spaces.
 * @param msg... one or more message arguments
 */
exports.log = function() {
    var msg = format.apply(null, arguments);
    writer.writeln(msg);
};

/**
 * Logs a message with the visual "error" representation, including the file name
 * and line number of the calling code.
 * @param msg... one or more message arguments
 * @function
 */
exports.error = traceHelper.bind(null, function() {
    var msg = format.apply(null, arguments);
    var location = format("(%s:%d)", this.sourceName(), this.lineNumber());
    writer.writeln(ONRED, BOLD, "[error]" + RESET, BOLD, msg, RESET, location);
});

/**
 * Logs a message with the visual "warn" representation, including the file name
 * and line number of the calling code.
 * @param msg... one or more message arguments
 * @function
 */
exports.warn = traceHelper.bind(null, function() {
    var msg = format.apply(null, arguments);
    var location = format("(%s:%d)", this.sourceName(), this.lineNumber());
    writer.writeln(ONYELLOW, BOLD, "[warn]" + RESET, BOLD, msg, RESET, location);
});

/**
 * Logs a message with the visual "info" representation, including the file name
 * and line number of the calling code.
 * @param {...} msg... one or more message arguments
 * @function
 */
exports.info = traceHelper.bind(null, function() {
    var msg = format.apply(null, arguments);
    var location = format("(%s:%d)", this.sourceName(), this.lineNumber());
    writer.writeln("[info]", BOLD, msg, RESET, location);
});

/**
 * Prints a stack trace of JavaScript execution at the point where it is called.
 * @param {...} msg... optional message arguments
 * @function
 */
exports.trace = traceHelper.bind(null, function() {
    var msg = format.apply(null, arguments);
    writer.writeln("Trace: " + msg);
    writer.write(this.scriptStackTrace);
});

/**
 * Tests that an expression is true and throws an exception if not.
 * @param expression the expression to test
 * @param {...} msg... one or more error messages
 * @function
 */
exports.assert = assertHelper;

/**
 * Creates a new timer under the given name. Call `console.timeEnd(name)` with
 * the same name to stop the timer and log the time elapsed.
 * @param {String} name the timer name
 */
exports.time = function(name) {
    if (name && !timers[name]) {
        timers[name] = java.lang.System.nanoTime();
    }
};

/**
 * Stops a timer created by a call to `console.time(name)` and logs the time elapsed.
 * @param {String} name the timer name
 */
exports.timeEnd = function(name) {
    var start = timers[name];
    if (start) {
        var time = Math.round((java.lang.System.nanoTime() - start) / 1000000);
        writer.writeln(name + ": " + time + "ms");
        delete timers[name];
        return time;
    }
    return undefined;
};

/**
 * Prints a list of all properties of an object.
 * @param {Object} obj the object
 */
exports.dir = function(obj) {
    require("ringo/shell").printResult(obj, writer);
};
