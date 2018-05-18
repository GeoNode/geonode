/**
 * @fileOverview A module for spawning processes, connecting to their
 * input/output/errput and returning their response codes.
 */

var {Stream, MemoryStream, TextStream} = require('io');
var fs = require('fs');
var arrays = require('ringo/utils/arrays');

function parseArguments(args) {
    // arguments may end with a {dir: "", env: {}} object
    var opts = (args.length > 1 && arrays.peek(args) instanceof Object) ?
            Array.pop(args) : {};
    // make command either a single string or an array of strings
    opts.command = args.length == 1 ? String(args[0]) : Array.map(args, String);
    return opts;
}

/**
 * Low-level function to spawn a new process. The function takes an object
 * argument containing the following properties where all properties except
 * command are optional:
 *
 *   * `command` a string or array of strings containing the command to execute
 *   * `dir` the directory to run the process in
 *   * `env` alternative environment variables. If null the process inherits the
 *     environment of the current process.
 *   * `binary` a boolean flag that uses raw binary streams instead of text streams
 *   * `encoding` the character encoding to use for text streams
 *
 * @param {Object} args an object containing the process command and options.
 * @returns a Process object
 * @see #Process
 */
var createProcess = exports.createProcess = function(args) {
    // convert arguments
    var {command, env, dir, binary, encoding} = args;
    dir = new java.io.File(dir || fs.workingDirectory());
    if (env && !Array.isArray(env)) {
        // convert env to an array of the form ["key=value", ...]
        env = [key + "=" + env[key] for (key in env)];
    } else if (!env) {
        env = null;
    }
    var process = java.lang.Runtime.getRuntime().exec(command, env, dir);
    var stdin = new Stream(process.getOutputStream());
    var stdout = new Stream(process.getInputStream());
    var stderr = new Stream(process.getErrorStream());
    if (!binary) {
        stdin = new TextStream(stdin, {charset: encoding});
        stdout = new TextStream(stdout, {charset: encoding});
        stderr = new TextStream(stderr, {charset: encoding});
    }
    /**
     * The Process object can be used to control and obtain information about a
     * subprocess started using [createProcess()](#createProcess).
     * @name Process
     * @class Process
     */
    return {
        /**
         * The process's input stream.
         * @name Process.prototype.stdin
         */
        stdin: stdin,
        /**
         * The process's output stream.
         * @name Process.prototype.stdout
         */
        stdout: stdout,
        /**
         * The process's error stream.
         * @name Process.prototype.stderr
         */
        stderr: stderr,
        /**
         * Wait for the process to terminate and return its exit status.
         * @name Process.prototype.wait
         * @function
         */
        wait: function() {
            return process.waitFor();
        },
        /**
         * Kills the subprocess.
         * @name Process.prototype.kill
         * @function
         */
        kill: function() {
            process.destroy();
        },
        /**
         * Connects the process's steams to the argument streams and starts threads to
         * copy the data asynchronously.
         * @param {Stream} input output stream to connect to the process's input stream
         * @param {Stream} output input stream to connect to the process's output stream
         * @param {Stream} errput input stream to connect to the process's error stream
         * @name Process.prototype.connect
         */
        connect: function(input, output, errput) {
            if (input) {
                spawn(function() {
                    input.copy(stdin);
                }).get();
            }
            spawn(function() {
                stdout.copy(output);
            }).get();
            spawn(function() {
                stderr.copy(errput);
            }).get();
        }
    };
}

/**
 * executes a given command and returns the
 * standard output.  If the exit status is non-zero,
 * throws an Error.
 * @param {String} command... command and optional arguments as single or multiple
 * string parameters
 * @param {Object} [options] options object. This may contain a `dir` string
 * property specifying the directory to run the process in and a `env`
 * object property specifying additional environment variable mappings.
 * @returns String the standard output of the command
 */
exports.command = function() {
    var args = parseArguments(arguments);
    var process = createProcess(args);
    var output= new MemoryStream(),
        errput = new MemoryStream();
    if (!args.binary) {
        output = new TextStream(output, {charset: args.encoding});
        errput = new TextStream(errput, {charset: args.encoding});
    }
    process.connect(null, output, errput);
    var status = process.wait();
    if (status != 0) {
        throw new Error("(" + status + ") " + errput.content);
    }
    return output.content;
};

/**
 * executes a given command, attached to this process's
 * output and error streams, and returns the exit status.
 * @param {String} command... command and optional arguments as single or multiple
 * string parameters
 * @param {Object} [options] options object. This may contain a `dir` string
 * property specifying the directory to run the process in and a `env`
 * object property specifying additional environment variable mappings.
 * @returns Number exit status
 */
exports.system = function() {
    var args = parseArguments(arguments);
    var process = createProcess(args);
    var output = system.stdout,
        errput = system.stderr;
    if (args.binary) {
        output = output.raw;
        errput = errput.raw;
    }
    process.connect(null, output, errput);
    return process.wait();
};

/**
 * Executes a given command quietly and returns the exit status.
 * @param {String} command... command and optional arguments as single or multiple
 * string parameters
 * @param {Object} [options] options object. This may contain a `dir` string
 * property specifying the directory to run the process in and a `env`
 * object property specifying additional environment variable mappings.
 * @returns Number exit status
 * @name status
 */
exports.status = function() {
    var process = createProcess(parseArguments(arguments));
    process.connect(null, dummyStream(), dummyStream());
    return process.wait();
};

function dummyStream() {
    return {
        writable: function() true,
        readable: function() false,
        seekable: function() false,
        write: function() this,
        flush: function() this,
        close: function() this
    }
}


