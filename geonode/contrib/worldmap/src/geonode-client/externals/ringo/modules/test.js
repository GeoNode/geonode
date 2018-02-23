/**
 * @fileOverview A test runner compliant to the
 * [CommonJS Unit Testing](http://wiki.commonjs.org/wiki/Unit_Testing/1.0)
 * specification.
 */

var strings = require("ringo/utils/strings");
var term = require("ringo/term");
var fs = require("fs");

export(
    "run",
    "jsDump",
    "getStackTrace",
    "getType"
);

var {
    AssertionError,
    ArgumentsError
} = require("./assert");

/**
 * Converts the value passed as argument into a nicely formatted and
 * indented string
 * @param {Object} value The value to convert into a string
 * @param {Number} lvl Optional indentation level (defaults to zero)
 * @returns The string representation of the object passed as argument
 * @type String
 */
function jsDump(value, lvl) {
    if (!lvl) {
        lvl = 0;
    }

    switch (getType(value)) {
        case "string":
            return jsDump.quote(value);
        case "boolean":
        case "number":
        case "nan":
        case "date":
        case "regexp":
            return value.toString();
        case "undefined":
        case "null":
            return String(value);
        case "function":
            if (getType(value.name) === "string" && value.name.length > 0) {
                return value.name;
            }
            return value.toSource();
        case "array":
            var buf = value.map(function(val) {
                return jsDump.indent(lvl + 1) + jsDump(val, lvl + 1);
            });
            return ["[", buf.join(",\n"), jsDump.indent(lvl) + "]"].join("\n");
        case "object":
            var buf = [];
            for (var propName in value) {
                buf.push(jsDump.indent(lvl + 1) + '"' + propName + '": ' + jsDump(value[propName], lvl + 1));
            }
            return ["{", buf.join(",\n"), jsDump.indent(lvl) + "}"].join("\n");
        case "java":
            return '<java:' + value.class.name + '>';
    }
}
jsDump.indent = function(lvl) {
    return strings.repeat(" ", 4 * lvl);
};
jsDump.quote = function(str) {
    return '"' + str.toString().replace(/"/g, '\\"').replace(/\n/g, '\\n') + '"';
};

/**
 * Returns the type of the object passed as argument. This is
 * heavily inspired by http://philrathe.com/articles/equiv and
 * tlrobinson's narwhal test module (http://github.com/tlrobinson/narwhal/)
 * @returns The type of the object passed as argument
 * @type String
 */
function getType(obj) {
    if (typeof(obj) === "string") {
        return "string";
    } else if (typeof(obj) === "boolean") {
        return "boolean";
    } else if (typeof (obj) === "number") {
        return (isNaN(obj) === true) ? "nan" : "number";
    } else if (typeof(obj) === "undefined") {
        return "undefined";
    } else if (obj === null) {
        return "null";
    } else if (obj instanceof Array) {
        return "array";
    } else if (obj instanceof Date) {
        return "date";
    } else if (obj instanceof RegExp) {
        return "regexp";
    } else if (obj instanceof Function) {
        return "function";
    } else if (obj instanceof java.lang.Object) {
        return "java";
    }
    return "object";
}

/**
 * Creates a stack trace and parses it for display.
 * @param {java.lang.StackTraceElement} trace The trace to parse. If not given
 * a stacktrace will be generated
 * @returns The parsed stack trace
 * @type String
 */
function getStackTrace(trace) {
    // create exception and fill in stack trace
    if (!trace) {
        var ex = new Packages.org.mozilla.javascript.EvaluatorException("");
        ex.fillInStackTrace();
        trace = ex.getScriptStack();
    }
    var stack = [];
    var el, fileName, lineNumber;
    for (var i = 0; i < trace.length; i += 1) {
        el = trace[i];
        if (el.fileName != null && el.lineNumber > -1) {
            // exclude all lines containing the unittest module itself
            // FIXME (ro): this is quite ugly, but it works ...
            if (el.fileName.indexOf(module.id) === 0 || el.fileName.indexOf("assert") === 0) {
                continue;
            }
            stack.push("at " + el.fileName + ":" + el.lineNumber);
        }
    }
    return stack;
};

/**
 * The main runner method. This method can be called with one, two or three
 * arguments: <code>run(scope)</code>, <code>run(scope, nameOfTest)</code>,
 * <code>run(scope, writer)</code> or <code>run(scope, nameOfTest, writer)</code>
 * @param {String|Object} scope Either the path to a module containing unit
 * tests to execute, or an object containing the exported test methods or nested scopes.
 * @param {String} name Optional name of a test method to execute
 * @param {Object} writer Optional writer to use for displaying the test results. Defaults
 * to TermWriter.
 */
function run(scope, name, writer) {
    if (arguments.length === 2) {
        if (typeof(arguments[1]) === "object") {
            writer = name;
            name = undefined;
        } else {
            writer = new TermWriter();
        }
    } else if (arguments.length === 1) {
        writer = new TermWriter();
    }
    if (typeof(scope) === "string") {
        scope = require(fs.resolve(fs.workingDirectory(), scope));
    }
    var summary = {
        "testsRun": 0,
        "passed": 0,
        "errors": 0,
        "failures": 0,
        "time": 0
    };
    writer.writeHeader();
    if (name != undefined) {
        executeTest(scope, name, summary, writer, []);
    } else {
        executeTestScope(scope, summary, writer, []);
    }
    scope = null;
    writer.writeSummary(summary);
    return summary.failures + summary.errors;
}

/**
 * Loops over all properties of a test scope and executes all methods whose
 * name starts with "test".
 * @param {Object} scope The scope object containing the test functions
 * @param {Object} summary An object containing summary information
 * @param {Object} writer A writer instance for displaying test results
 * @param {Array} path An array containing property path segments
 */
function executeTestScope(scope, summary, writer, path) {
    // loop over all exported properties and see if there are test methods to run
    for (var name in scope) {
        var value = scope[name];
        if (name === "test" || !strings.startsWith(name, "test")) {
            continue;
        }
        executeTest(scope, name, summary, writer, path);
    }
    return;
};

/**
 * Executes a single test, which can be either a single test method
 * or a test submodule.
 * @param {Object} scope The scope object containing the test
 * @param {String} name The name of the test to execute
 * @param {Object} summary An object containing summary information
 * @param {Object} writer A writer instance for displaying test results
 * @param {Array} path An array containing property path segments
 */
function executeTest(scope, name, summary, writer, path) {
    var value = scope[name];
    if (value instanceof Function) {
        writer.writeTestStart(name);
        var start = null;
        var time = 0;
        try {
            // execute setUp, if defined
            if (typeof(scope.setUp) === "function") {
                scope.setUp();
            }
            // execute test function
            start = new Date();
            value();
            time = (new Date()).getTime() - start.getTime();
            writer.writeTestPassed(time);
            summary.passed += 1;
        } catch (e) {
            if (!(e instanceof AssertionError) && !(e instanceof ArgumentsError)) {
                e = new EvaluationError(e);
            }
            writer.writeTestFailed(e);
            if (e instanceof AssertionError) {
                summary.failures += 1;
            } else {
                summary.errors += 1;
            }
        } finally {
            // execute tearDown, if defined
            if (typeof(scope.tearDown) === "function") {
                scope.tearDown();
            }
            summary.testsRun += 1;
            summary.time += time;
        }
    } else if (value.constructor === Object) {
        writer.enterScope(name);
        executeTestScope(value, summary, writer, path.concat([name]));
        writer.exitScope(name);
    }
    return;
}



/*******************************************
 *****  T E R M I N A L   W R I T E R  *****
 *******************************************/



/**
 * Constructs a new TermWriter instance
 * @class Instances of this class represent a writer for displaying test results
 * in the shell
 * @returns A newly created TermWriter instance
 * @constructor
 */
var TermWriter = function() {
    this.indent = "";
    return this;
};

/** @ignore */
TermWriter.prototype.toString = function() {
    return "[TermWriter]";
};

/**
 * Write a header at the beginning of a unit test(suite)
 */
TermWriter.prototype.writeHeader = function() {
    term.writeln("================================================================================");
    return;
};

/**
 * Notification that we're entering a new test scope.
 * @param name the name of the test scope
 */
TermWriter.prototype.enterScope = function(name) {
    term.writeln(this.indent, "+ Running", name, "...");
    this.indent += "  ";
};

/**
 * Notification that we're leaving a test scope.
 * @param name the name of the test scope
 */
TermWriter.prototype.exitScope = function(name) {
    this.indent = this.indent.substring(2);
};

/**
 * Display the beginning of a test function execution
 * @param {String} name The name of the test function about to be executed
 */
TermWriter.prototype.writeTestStart = function(name) {
    term.write(this.indent, "+ Running", name, "...");
    return;
};

/**
 * Display a passed test method execution
 * @param {Number} time The time the execution of the test method took
 */
TermWriter.prototype.writeTestPassed = function(time) {
    term.writeln(term.BOLD, " PASSED", term.RESET, "(" + time + " ms)");
    return;
};

/**
 * Display a failed test
 * @param {Object} exception The exception thrown during test method execution
 */
TermWriter.prototype.writeTestFailed = function(exception) {
    term.writeln(term.BOLD, term.WHITE, term.ONRED, " FAILED ");
    exception.message.split(/\n/).forEach(function(line) {
        term.writeln("  ", term.BOLD, term.RED, line);
    });
    if (exception.stackTrace != null) {
        exception.stackTrace.forEach(function(line) {
            term.writeln("  ", term.BOLD, line);
        });
    }
    term.writeln("");
    return;
};

/**
 * Display the summary of a unit test(suite) execution
 * @param {Object} summary The unit test summary
 */
TermWriter.prototype.writeSummary = function(summary) {
    if (summary.testsRun > 0) {
        term.writeln("--------------------------------------------------------------------------------");
        term.writeln("Executed", summary.testsRun, "tests in", summary.time, "ms ");
        term.writeln(term.BOLD, "Passed", summary.passed + ";", "Failed", summary.failures + ";", "Errors", summary.errors + ";");
    } else {
        term.writeln("No tests found");
    }
    return;
};
/**
 * Creates a new EvaluationError instance
 * @class Instances of this class represent an exception thrown when evaluating
 * a test file or a single test function
 * @param {Object} messageOrException Either a message string or the exception
 * thrown when evaluating
 * @returns A newly created EvaluationError instance
 * @constructor
 * @exteds TestException
 */
function EvaluationError(messageOrException) {
    var message = undefined;
    var exception = null;
    var stackTrace = null;
    var fileName = null;
    var lineNumber = -1;

    Object.defineProperty(this, "message", {
        get: function() {
            return message;
        }
    });

    Object.defineProperty(this, "stackTrace", {
        get: function() {
            return stackTrace;
        }
    });

    Object.defineProperty(this, "fileName", {
        get: function() {
            return fileName;
        }
    });

    Object.defineProperty(this, "lineNumber", {
        get: function() {
            return lineNumber;
        }
    });

    /**
     * Main constructor body
     */
    if (messageOrException instanceof Error) {
        exception = messageOrException;
    } else {
        message = messageOrException;
    }

    if (exception != null) {
        if (exception.rhinoException != null) {
            var e = exception.rhinoException;
            message += e.details();
            stackTrace = getStackTrace(e.getStackTrace());
        } else if (exception instanceof Error) {
            message = exception.message;
        }
        if (!stackTrace) {
            // got no stack trace, so add at least filename and line number
            fileName = exception.fileName || null;
            lineNumber = exception.lineNumber || null;
        }
    }
    return this;
};
EvaluationError.prototype = new Error();

/**
 * Executed when called from the command line
 */
if (require.main == module.id) {
    if (system.args.length == 1) {
        term.writeln("Usage: bin/ringo test test/file1 test/file2");
    } else {
        var writer = new TermWriter();
        var failures = 0;
        for (var i=1; i<system.args.length; i+=1) {
            failures += this.run(system.args[i], writer);
        }
        system.exit(failures);
    }
}
