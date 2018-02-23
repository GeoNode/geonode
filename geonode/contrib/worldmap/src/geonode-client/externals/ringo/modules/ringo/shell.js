/**
 * @fileOverview provides functions to work with the Ringo shell.
 */

var system = require('system');
var term = require('ringo/term');

export('write', 'writeln', 'read', 'readln', 'start', 'quit',
       'printResult', 'printError');

try {
    var input = new Packages.jline.ConsoleReader();
} catch (x) {
    // fall back to plain standard input
}

/**
 * Write 0..n arguments to standard output.
 */
function write() {
    var length = arguments.length;
    var out = system.stdout;
    for (var i = 0; i < length; i++) {
        out.write(String(arguments[i]));
        if (i < length - 1)
            out.write(' ');
    }
}

/**
 * Write 0..n arguments to standard output, followed by a newline.
 */
function writeln() {
    write.apply(this, arguments);
    system.stdout.writeLine('');
}

/**
 * Read a single character from the standard input.
 */
function read() {
    if (!input) {
        throw new Error('jline not installed');
    }
    return String.fromCharCode(input.readVirtualKey());
}

/**
 * Read a single line from the standard input.
 * @param {String} prompt optional prompt to display
 * @param {String} echoChar character to use as echo,
 *         e.g. '*' for passwords or '' for no echo.
 */
function readln(prompt, echoChar) {
    prompt = prompt || '';
    if (input) {
        if (typeof echoChar == 'string') {
            var echo = echoChar == '' ?
                   new java.lang.Character(0) :
                   new java.lang.Character(echoChar.charCodeAt(0));
            return input.readLine(prompt, echo);
        }
        return input.readLine(prompt);
    } else {
        system.stdout.write(prompt);
        return system.stdin.readLine().trim();
    }
}

/**
 * Start the shell programmatically. This uses the current thread and thus will not
 * return. You should therefore call this function as the last statement in your script.
 * Terminating the shell will exit the program.
 * @since 0.5
 */
function start(engine) {
    engine = engine || require('ringo/engine').getRhinoEngine();
    new org.ringojs.tools.RingoShell(engine).run();
}

/**
 * Quit the shell and exit the JVM.
 * @param {Number} status optional integer exit status code (default is 0)
 */
function quit(status) {
   java.lang.System.exit(status || 0);
}

var styles = {
    'number': term.BLUE,
    'string': term.GREEN,
    'function': term.CYAN,
    'boolean': term.YELLOW,
    'null': term.BOLD,
    'date': term.MAGENTA,
    'java': term.MAGENTA,
    'custom': term.RED
}

function convert(value, nesting, visited) {
    var type = typeof value;
    var retval = {type: type};
    switch (type) {
        case 'number':
            retval.string = String(value);
            break;
        case 'string':
            retval.string  = "'" + value.replace(/'/g, "\\'") + "'";
            break;
        case 'function':
            retval.string = "[Function]";
            break;
        case 'boolean':
            retval.string =  String(value);
            break;
        case 'object':
            if (value === null) {
                retval.type = retval.string = 'null';
                break;
            }
            if (visited.indexOf(value) > -1) {
                retval.type = "cyclic";
                retval.string = "[CyclicRef]";
                break;
            }
            visited.push(value);
            if (value instanceof java.lang.Object && typeof value.getClass === "function") {
                retval.type = "java";
                retval.string = "[" + value.getClass().getName() + " "
                        + String(value) + "]";
            } else if (value instanceof Date) {
                retval.type = "date";
                retval.string = String(value);
            } else if (Array.isArray(value)) {
                if (nesting > 1) {
                    retval.string = "[...]";
                } else {
                    retval.type = "array";
                    retval.items = [];
                    var count = 0;
                    for (var i = 0; i < value.length; i++) {
                        var part = convert(value[i], nesting + 1, visited);
                        count += (part.string && part.string.length || part.count || 0) + 2;
                        retval.items.push(part);
                    }
                    retval.count = count;
                }
            } else if (value.toString !== Object.prototype.toString) {
                // if object provides its own toString we assume it wants to use it
                retval.type = "custom";
                retval.string = value.toString();
                break;
            } else {
                if (nesting > 1) {
                    retval.string = "{...}";
                } else {
                    retval.items = [];
                    var keys = Object.keys(value);
                    count = 0;
                    for (i = 0; i < keys.length; i++) {
                        part = convert(value[keys[i]], nesting + 1, visited);
                        count += String(keys[i]).length + 4;
                        count += part.string && part.string.length || part.count || 0;
                        retval.items.push({
                            key: keys[i] + ": ",
                            value: part
                        });
                    }
                    retval.count = count;
                }
            }
            break;
        case 'undefined':
            retval = {};
            break;
        default:
            retval.string = String(value);
            break;
    }
    return retval;
}

function printResult(value, writer) {
    if (typeof value !== "undefined") {
        writer = writer || term;
        printValue(convert(value, 0, []), writer, 0);
        writer.writeln();
    }
}

function printValue(value, writer, nesting) {
    if (value.string) {
        var style = styles[value.type] || "";
        writer.write(style + value.string + term.RESET);
    } else if (value && value.items) {
        var multiline = value.count > 60;
        var isArray = value.type === "array";
        var length = value.items.length;
        if (length === 0) {
            writer.write(isArray ? "[]" : "{}");
            return;
        }
        var opener = isArray ? "[" : "{";
        if (multiline && nesting > 0) {
            writer.write(opener + "\n  ");
            for (j = 0; j < nesting; j++)
                writer.write("  ");
        } else {
            writer.write(opener + " ");
        }
        if (isArray) {
            for (var i = 0; i < length; i++) {
                printValue(value.items[i], writer, nesting + 1);
                if (i < length - 1) {
                    if (multiline) {
                        writer.write(",\n  ");
                        for (var j = 0; j < nesting; j++)
                            writer.write("  ");
                    } else {
                        writer.write(", ");
                    }
                }
            }
            writer.write(term.RESET + " ]");
        } else {
            for (i = 0; i < length; i++) {
                writer.write(value.items[i].key);
                printValue(value.items[i].value, writer, nesting + 1);
                if (i < length - 1) {
                    if (multiline) {
                        writer.write(",\n  ");
                        for (j = 0; j < nesting; j++)
                            writer.write("  ");
                    } else {
                        writer.write(", ");
                    }
                }
            }
            writer.write(term.RESET + " }");
        }
    }
}

/**
 * @param {Exception} xcept
 * @param {Boolean} verbose
 */
function printError(xcept, errors, verbose) {
    if (xcept instanceof org.mozilla.javascript.RhinoException) {
        term.writeln(term.BOLD, term.RED, xcept.details());
    } else {
        term.writeln(term.BOLD, term.RED, xcept.toString());
    }
    for (var i = 0, l = errors.length; i < l; i++) {
        term.writeln(term.GREEN, errors[i]);
    }
    if (typeof xcept.getScriptStackTrace === "function") {
        term.write(xcept.getScriptStackTrace());
    }
    if (verbose) {
        if (typeof xcept.getWrappedException === "function") {
            xcept = xcept.getWrappedException();
        }
        term.writeln(term.BOLD, "Java Exception:")
        xcept.printStackTrace(system.stdout.raw || System.out);
    }
}
