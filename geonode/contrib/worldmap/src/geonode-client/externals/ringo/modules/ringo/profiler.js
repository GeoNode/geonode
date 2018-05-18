/**
 * @fileOverview A profiler for measuring execution time of JavaScript functions. Note that
 * you need to run with optimization level -1 for profiling to work. Running
 * the profiler on optimized code will produce no data.
 */

var strings = require('ringo/utils/strings');
var log = require('ringo/logging').getLogger(module.id);
var Buffer = require('ringo/buffer').Buffer;

export('profile', 'Profiler');

/**
 * Convenience function for profiling the invocation of a function.
 * @param {Function} func the function to profile
 * @param {number} maxFrames optional maximal number of frames to include
 * @returns {Object} an object with the following properties:
 *  <ul><li>result: the value returned by the function, if any</li>
 *  <li>error: the error thrown by the function, if any</li>
 *  <li>profiler: the Profiler instance used to profile the invocation</li></ul>
 */
function profile(func, maxFrames) {
    var engine = require("ringo/engine");
    if (engine.getOptimizationLevel() > -1) {
        log.warn("Profiling with optimization enabled will not produce any results.",
                 "Please set the optimization level to -1 when using the profiler.");
    }
    var profiler = new Profiler();
    var result, error;
    profiler.attach();
    try {
        result = func();
    } catch (e) {
        error = e;
    } finally {
        profiler.detach();
    }
    return {
        result: result,
        error: error,
        profiler: profiler
    }
}

/**
 * A class for measuring the frequency and runtime of function invocations.
 */
function Profiler() {
    var stack = [];
    var frames = {};
    var nanoTime = java.lang.System.nanoTime;

    this.getScriptFrame = function(cx, script) {
        if (!script.isFunction()) {
            return null;
        }
        var name = getScriptName(script);
        var frame = frames[name];
        if (!frame) {
            frame = new Frame(name);
            frames[name] = frame;
        }
        return frame;
    };

    var getScriptName = function(script) {
        if (script.isFunction()) {
            var name = [script.sourceName,  " #", script.lineNumbers[0]];
            if (script.functionName) {
                name.push(": ", script.functionName);
            }
            return name.join("");
        } else {
            return script.sourceName;
        }
    };

    this.getFrames = function() {
        var list = [];
        for each (var frame in frames) {
            list.push(frame);
        }
        // sort list according to total runtime
        list = list.sort(function(a, b) {
            return b.getSelftime() - a.getSelftime();
        });
        return list;
    };

    this.formatResult = function(maxFrames) {
        var list = this.getFrames();
        // cut list to maxFrames elements
        if (typeof maxFrames == "number") {
            list.length = maxFrames;
        }
        var count = 0;
        var maxLength = 0;
        // find common prefix in path names
        var commonPrefix = list.reduce(function(previous, current) {
            return strings.getCommonPrefix(previous, current.name);
        }, "");
        var lines = [];
        for each (var item in list) {
            var str = item.renderLine(commonPrefix.length);
            maxLength = Math.max(maxLength, str.length);
            lines.push(str);
        }
        var buffer = new Buffer();
        buffer.writeln("     total  average  calls    path");
        for (var i = 1; i < maxLength; i++) {
            buffer.write("-");
        }
        buffer.writeln();
        buffer.write(lines.join("\n"));
        return buffer.toString();
    };

    this.toString = function() {
        return this.formatResult(null);
    };

    function Frame(name) {

        // The timer for the current invocation of this frame.
        // This is an object containing start and end timestamp properties and
        // a subTimers array property containing timers for functions directly
        // invoked from this frame.
        var currentTimer;
        var timerStack = [];     // Timer stack for other currently active invocations of this frame
        var finishedTimers = []; // Timer list of finished invocations of this frame
        this.name = name;

        this.onEnter = function(cx, activation, thisObj, args) {
            if (currentTimer) {
                timerStack.push(currentTimer);
            }
            var now = nanoTime();
            currentTimer = {
                name: name,
                start: now,
                subTimers: []
                // invoker: stack.length ? stack[stack.length - 1].name : null
            };
            stack.push(this);
        };

        this.onExceptionThrown = function(cx, ex) {
        };

        this.onExit = function(cx, byThrow, resultOrException) {
            currentTimer.end = nanoTime();
            stack.pop();
            if (stack.length > 0) {
                stack[stack.length - 1].addSubTimer(currentTimer);
            }
            finishedTimers.push(currentTimer);
            currentTimer = timerStack.pop();
        };

        this.addSubTimer = function(subTimer) {
            currentTimer.subTimers.push(subTimer);
        };

        this.getSelftime = function() {
            return finishedTimers.reduce(
                function(prev, e) {
                    // add this timer's runtime minus the accumulated sub-timers
                    return (prev + e.end - e.start) - e.subTimers.reduce(function(prev, e) {
                        return prev + e.end - e.start;
                    }, 0);
                }, 0
            );
        };

        this.getRuntime = function() {
            return finishedTimers.reduce(
                function(prev, e) {
                    return prev + (e.end - e.start);
                }, 0
            );
        };

        this.countInvocations = function() {
            return finishedTimers.length;
        };

        this.renderLine = function(prefixLength) {
            var runtime = this.getSelftime() / 1000000;
            var count = this.countInvocations();
            var formatter = new java.util.Formatter();
            formatter.format("%1$7.0f ms %2$5.0f ms %3$6.0f    %4$s",
                    runtime, Math.round(runtime / count), count, name.slice(prefixLength));
            return formatter.toString();
        };

        return new org.mozilla.javascript.debug.DebugFrame(this);
    }

    var profiler = new org.ringojs.util.DebuggerBase(this);
    profiler.debuggerScript = module.id + ".js";
    return profiler;
}
