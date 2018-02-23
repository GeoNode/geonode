/**
 * @fileoverview <p>This module provides an implementation of the system module
 * compliant to the <a href="http://wiki.commonjs.org/wiki/System/1.0">CommonJS
 * System/1.0</a> specification.</p>
 *
 * <p>Beyond the standard, a "print" function and some properties for Narwhal
 * compatibility are provided.</p>
 */

var stdin, stdout, stderr;
var System = java.lang.System;

/**
 * A TextStream to read from stdin.
 * @name stdin
 */
Object.defineProperty(exports, "stdin", {
    get: function() {
        if (!stdin) {
            var {Stream, TextStream} = require('io');
            stdin = new TextStream(new Stream(System['in']));
        }
        return stdin;
    },
    set: function(value) {
        stdin = value;
    }, configurable: true, enumerable: true
});

/**
 * A TextStream to write to stdout.
 * @name stdout
 */
Object.defineProperty(exports, "stdout", {
    get: function() {
        if (!stdout) {
            var {Stream, TextStream} = require('io');
            stdout = new TextStream(new Stream(System.out));
        }
        return stdout;
    },
    set: function(value) {
        stdout = value;
    }, configurable: true, enumerable: true
});

/**
 * A TextStream to write to stderr.
 * @name stderr
 */
Object.defineProperty(exports, "stderr", {
    get: function() {
        if (!stderr) {
            var {Stream, TextStream} = require('io');
            stderr = new TextStream(new Stream(System.err));
        }
        return stderr;
    },
    set: function(value) {
        stderr = value;
    }, configurable: true, enumerable: true
});

/**
 * A utility function to write to stdout.
 */
exports.print = function() {
    exports.stdout.print.apply(exports.stdout, arguments);
};

/**
 * An array of strings representing the command line arguments passed to the running script.
 */
exports.args = global.arguments || [];

/**
 * An object containing our environment variables.
 */
exports.env = new ScriptableMap(System.getenv());

/**
 * Terminates the current process.
 * @param {number} status The exit status, defaults to 0.
 */
exports.exit = function(status) {
    System.exit(status || 0);
};

// Narwhal compatibility
var engine = org.ringojs.engine.RhinoEngine.getEngine(global);
var home = engine.getRingoHome();
/** @ignore */
exports.prefix = home.getPath();
/** @ignore */
exports.prefixes = [exports.prefix];
/** @ignore */
exports.engine = "rhino";
/** @ignore */
exports.engines = ["rhino", "default"];
