/**
 * @fileOverview Assertion library covering the
 * [CommonJS Unit Testing](http://wiki.commonjs.org/wiki/Unit_Testing/1.0) specification
 * and a few additional convenience methods. 
 */

export(
   "AssertionError",
   "ArgumentsError",
   "fail",
   // commonjs assertion methods
   "ok",
   "equal",
   "notEqual",
   "deepEqual",
   "notDeepEqual",
   "strictEqual",
   "notStrictEqual",
   "throws",
   // custom assertion methods
   "isTrue",
   "isFalse",
   "matches",
   "stringContains",
   "isNull",
   "isNotNull",
   "isUndefined",
   "isNotUndefined",
   "isNaN",
   "isNotNaN"
);

var {
    jsDump,
    getType,
    getStackTrace
} = require("./test");

/**
* @param {Object} args The arguments array.
* @param {Number} argsExpected The number of expected arguments
* @returns The comment appended to the expected arguments, if any
* @type String
*/
function evalArguments(args, argsExpected) {
    if (!(args.length == argsExpected ||
            (args.length == argsExpected + 1 && getType(args[args.length - 1]) == "string"))) {
        throw new ArgumentsError("Insufficient arguments passed to assertion function");
    }
    return args[argsExpected];
};

/**
 * Deep-compares both arguments
 * @param {Object} value1 The argument to be compared
 * @param {Object} value2 The argument to be compared to
 * @returns True if arguments are equal, false otherwise
 * @type Boolean
 */
function isDeepEqual(value1, value2) {
    if (value1 === value2) {
        return true;
    } else if (value1 instanceof Date && value2 instanceof Date) {
        return value1.getTime() === value2.getTime();
    } else if (typeof(value1) != "object" || typeof(value2) != "object") {
        return value1 == value2;
    } else {
        return objectsAreEqual(value1, value2);
    }
}

/**
 * Returns true if the objects passed as argument are equal
 * @param {Object} value1 The object to be compared
 * @param {Object} value2 The object to be compared to
 * @returns True if the objects are equal, false otherwise
 * @type Boolean
 */
function objectsAreEqual(obj1, obj2) {
    if (isNullOrUndefined(obj1) || isNullOrUndefined(obj2)) {
        return false;
    }
    // the 1.0 spec (and Unittest/B) speaks of comparing the prototype
    // property, which is only set for constructor functions (for instances
    // it's undefined). plus only owned properties are compared, leading
    // to two objects being equivalent even if their prototypes have
    // different properties. instead using Object.getPrototypeOf()
    // to compare the prototypes of two objects
    // see also http://groups.google.com/group/commonjs/msg/501a7e3cd9a920e5
    if (Object.getPrototypeOf(obj1) !== Object.getPrototypeOf(obj2)) {
        return false;
    }
    // compare object keys (objects *and* arrays)
    var keys1 = getOwnKeys(obj1);
    var keys2 = getOwnKeys(obj2);
    var propsAreEqual = keys1.length === keys2.length && keys1.every(function(name, idx) {
        return name === keys2[idx] && isDeepEqual(obj1[name], obj2[name]);
    });
    if (propsAreEqual === false) {
        return propsAreEqual;
    }
    // array comparison
    if (getType(obj1) === "array") {
        return obj1.length === obj2.length && obj1.every(function(value, idx) {
            return isDeepEqual(value, obj2[idx]);
        });
    }
    return true;
}

/**
 * Returns true if the argument is null or undefined
 * @param {Object} obj The object to test
 * @returns True if the argument is null or undefined
 * @type Boolean
 */
function isNullOrUndefined(obj) {
    return obj === null || obj === undefined;
}

/**
 * Returns the names of owned properties of the object passed as argument.
 * Note that this only includes those properties for which hasOwnProperty
 * returns true
 * @param {Object} obj The object to return its propery names for
 * @returns The property names
 * @type Array
 */
function getOwnKeys(obj) {
    return [key for (key in obj) if (Object.prototype.hasOwnProperty.call(obj, key))].sort();
}

/**
 * Basic failure method
 * @param {Object|String} options An object containing optional "message", "actual"
 * and "expected" properties, or alternatively a message string
 * @throws AssertionError
 */
function fail(options) {
    throw new AssertionError(options);
}

/**
 * Prepends the comment to the message, if given
 * @returns The message
 * @type String
 */
function prependComment(message, comment) {
    if (getType(comment) === "string" && comment.length > 0) {
        return comment + "\n" + message;
    }
    return message;
}


/***************************
 *****   E R R O R S   *****
 ***************************/



/**
 * Constructs a new AssertionError instance
 * @class Instances of this class represent an assertion error
 * @param {Object} options An object containing error details
 * @param.message {String} The error message
 * @param.actual {Object} The actual value
 * @param.expected {Object} The expected value
 * @constructor
 * @augments Error
 */
function AssertionError(options) {
    // accept a single string argument
    if (getType(options) === "string") {
        options = {
            "message": options
        };
    }
    var stackTrace = getStackTrace();

    Object.defineProperty(this, "name", {
        get: function() {
            return "AssertionError";
        }
    });

    Object.defineProperty(this, "message", {
        get: function() {
            return options.message;
        }
    });

    Object.defineProperty(this, "actual", {
        get: function() {
            return options.actual;
        }
    });

    Object.defineProperty(this, "expected", {
        get: function() {
            return options.expected;
        }
    });

    Object.defineProperty(this, "stackTrace", {
        get: function() {
            return stackTrace;
        }
    });

    return this;
};

/** @ignore */
AssertionError.prototype = new Error();

/** @ignore */
AssertionError.toString = function() {
    return "[AssertionError]";
};

/** @ignore */
AssertionError.prototype.toString = function() {
    return "[AssertionError '" + this.message + "']";
};

/**
 * Creates a new ArgumentsError instance
 * @class Instances of this class represent an error thrown if insufficient
 * arguments have been passed to an assertion function
 * @param {String} message The exception message
 * @returns A newly created ArgumentsError instance
 * @constructor
 */
function ArgumentsError(message) {

    var stackTrace = getStackTrace();

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

    return this;
};

/** @ignore */
ArgumentsError.prototype = new Error();

/** @ignore */
ArgumentsError.toString = function() {
    return "[ArgumentsError]";
};

/** @ignore */
ArgumentsError.prototype.toString = function() {
    return "[ArgumentsError '" + this.message + "']";
};




/*******************************************************************
 *****   C O M M O N J S   A S S E R T I O N   M E T H O D S   *****
 *******************************************************************/



/**
 * Checks if the value passed as argument is truthy.
 * @param {Object} value The value to check for truthiness
 * @throws ArgumentsError
 * @throws AssertionError
 */
function ok(value) {
    var comment = evalArguments(arguments, arguments.callee.length);
    if (!!value === false) {
        fail({
            "message": prependComment("Expected " + jsDump(value) + " to be truthy", comment),
            "actual": value,
            "expected": true
        });
    }
    return;
}

/**
 * Checks if the values passed as arguments are equal.
 * @param {Object} actual The actual value
 * @param {Object} expected The expected value
 * @throws ArgumentsError
 * @throws AssertionError
 */
function equal(actual, expected) {
    var comment = evalArguments(arguments, arguments.callee.length);
    if (actual != expected) {
        fail({
            "message": prependComment("Expected " + jsDump(expected) + ", got " + jsDump(actual), comment),
            "actual": actual,
            "expected": expected
        });
    }
    return;
}

/**
 * Checks if the values passed as arguments are not equal.
 * @param {Object} actual The actual value
 * @param {Object} expected The expected value
 * @throws ArgumentsError
 * @throws AssertionError
 */
function notEqual(actual, expected) {
    var comment = evalArguments(arguments, arguments.callee.length);
    if (actual == expected) {
        fail({
            "message": prependComment("Expected different value than " + jsDump(expected) +
                       ", got equivalent value " + jsDump(actual), comment),
            "actual": actual,
            "expected": expected
        });
    }
    return;
}

/**
 * Checks if the values passed as arguments are deep equal
 * @param {Object} actual The actual value
 * @param {Object} expected The expected value
 * @throws ArgumentsError
 * @throws AssertionError
 */
function deepEqual(actual, expected) {
    var comment = evalArguments(arguments, arguments.callee.length);
    if (isDeepEqual(actual, expected) === false) {
        fail({
            "message": prependComment("Expected " + jsDump(expected) + ", got " + jsDump(actual), comment),
            "actual": actual,
            "expected": expected
        });
    }
    return;
}

/**
 * Checks if the values passed as arguments are not deep equal
 * @param {Object} actual The actual value
 * @param {Object} expected The expected value
 * @throws ArgumentsError
 * @throws AssertionError
 */
function notDeepEqual(actual, expected) {
    var comment = evalArguments(arguments, arguments.callee.length);
    if (isDeepEqual(actual, expected) === true) {
        fail({
            "message": prependComment("Expected different value than " + jsDump(expected) +
                       ", got deep equal value " + jsDump(actual), comment),
            "actual": actual,
            "expected": expected
        });
    }
    return;
}

/**
 * Checks if the values passed as arguments are strictly equal
 * @param {Object} actual The actual value
 * @param {Object} expected The expected value
 * @throws ArgumentsError
 * @throws AssertionError
 */
function strictEqual(actual, expected) {
    var comment = evalArguments(arguments, arguments.callee.length);
    if (actual !== expected) {
        fail({
            "message": prependComment("Expected " + jsDump(expected) + ", got " + jsDump(actual), comment),
            "actual": actual,
            "expected": expected
        });
    }
    return;
}

/**
 * Checks if the values passed as arguments are not strictly equal
 * @param {Object} actual The actual value
 * @param {Object} expected The expected value
 * @throws ArgumentsError
 * @throws AssertionError
 */
function notStrictEqual(actual, expected) {
    var comment = evalArguments(arguments, arguments.callee.length);
    if (actual === expected) {
        fail({
            "message": prependComment("Expected different value than " + jsDump(expected) +
                       ", got strictly equal value " + jsDump(actual), comment),
            "actual": actual,
            "expected": expected
        });
    }
    return;
}

/**
 * Checks if the function passed as argument throws a defined exception.
 * @param {Object} func The function to call
 * @param {Object} expectedError Optional object expected to be thrown when executing
 * the function
 * @throws ArgumentsError
 * @throws AssertionError
 */
function throws(func, expectedError) {
    if (!(func instanceof Function)) {
        throw new ArgumentsError("First argument to throws() must be a function");
    }
    try {
        func();
    } catch (e) {
        var isExpected = false;
        var thrown = e;
        if (expectedError == null) {
            // accept everything
            isExpected = true;
        } else if (expectedError != null && e != null) {
            // check if exception is the one expected
            switch (typeof(expectedError)) {
                case "string":
                    isExpected = (e.name === expectedError || e === expectedError);
                    break;
                case "function":
                    // this is true for all JS constructors and Java classes!
                    isExpected = (e instanceof expectedError ||
                                      (thrown = e.rhinoException) instanceof expectedError ||
                                      (thrown = e.javaException) instanceof expectedError);
                    break;
                case "number":
                case "boolean":
                default:
                    isExpected = (e === expectedError);
                    break;
            }
        }
        if (!isExpected) {
            fail({
                "message": "Expected " + jsDump(expectedError) +
                           " to be thrown, but got " + jsDump(e) + " instead",
                "actual": e,
                "expected": expectedError
            });
        }
        return;
    }
    if (expectedError != null) {
        fail("Expected exception " + jsDump(expectedError) + " to be thrown");
    }
    fail("Expected exception to be thrown");
}



/***************************************************************
 *****   C U S T O M   A S S E R T I O N   M E T H O D S   *****
 ***************************************************************/



/**
 * Checks if the value passed as argument is boolean true.
 * @param {Object} val The value that should be boolean true.
 * @throws ArgumentsError
 * @throws AssertionError
 */
function isTrue(value) {
    var comment = evalArguments(arguments, arguments.callee.length);
    if (getType(value) !== "boolean") {
        throw new ArgumentsError("Invalid argument to assertTrue(boolean): " +
                jsDump(value));
    } else if (value !== true) {
        fail({
            "message": prependComment("Expected true, got " + jsDump(value), comment),
            "actual": value,
            "expected": true
        });
    }
    return;
}

/**
 * Checks if the value passed as argument is boolean false.
 * @param {Object} val The value that should be boolean false.
 * @throws ArgumentsError
 * @throws AssertionError
 */
function isFalse(value) {
    var comment = evalArguments(arguments, arguments.callee.length);
    if (getType(value) !== "boolean") {
        throw new ArgumentsError("Invalid argument to assertFalse(boolean): " +
                             jsDump(value));
    } else if (value === true) {
        fail({
            "message": prependComment("Expected false, got " + jsDump(value), comment),
            "actual": value,
            "expected": false
        });
    }
    return;
}

/**
 * Checks if the value passed as argument is null.
 * @param {Object} val The value that should be null.
 * @throws ArgumentsError
 * @throws AssertionError
 */
function isNull(value) {
    var comment = evalArguments(arguments, arguments.callee.length);
    if (value !== null) {
        fail({
            "message": prependComment("Expected " + jsDump(value) + " to be null", comment),
            "actual": value,
            "expected": null
        });
    }
    return;
}

/**
 * Checks if the value passed as argument is not null.
 * @param {Object} val The value that should be not null.
 * @throws ArgumentsError
 * @throws AssertionError
 */
function isNotNull(value) {
    var comment = evalArguments(arguments, arguments.callee.length);
    if (value === null) {
        fail({
            "message": prependComment("Expected " + jsDump(value) + " to be not null", comment),
            "actual": value,
        });
    }
    return;
}

/**
 * Checks if the value passed as argument is undefined.
 * @param {Object} val The value that should be undefined.
 * @throws ArgumentsError
 * @throws AssertionError
 */
function isUndefined(value) {
    var comment = evalArguments(arguments, arguments.callee.length);
    if (value !== undefined) {
        fail({
            "message": prependComment("Expected " + jsDump(value) + " to be undefined", comment),
            "actual": value,
            "expected": undefined
        });
    }
    return;
}

/**
 * Checks if the value passed as argument is not undefined.
 * @param {Object} val The value that should be not undefined.
 * @throws ArgumentsError
 * @throws AssertionError
 */
function isNotUndefined(value) {
    var comment = evalArguments(arguments, arguments.callee.length);
    if (value === undefined) {
        fail({
            "message": prependComment("Expected argument to be not undefined", comment),
            "actual": value,
        });
    }
    return;
}

/**
 * Checks if the value passed as argument is NaN.
 * @param {Object} val The value that should be NaN.
 * @throws ArgumentsError
 * @throws AssertionError
 */
function isNaN(value) {
    var comment = evalArguments(arguments, arguments.callee.length);
    if (global.isNaN(value) === false) {
        fail({
            "message": prependComment("Expected " + jsDump(value) + " to be NaN", comment),
            "actual": value,
            "expected": NaN
        });
    }
    return;
}

/**
 * Checks if the value passed as argument is not NaN.
 * @param {Object} val The value that should be not NaN.
 * @throws ArgumentsError
 * @throws AssertionError
 */
function isNotNaN(value) {
    var comment = evalArguments(arguments, arguments.callee.length);
    if (global.isNaN(value) === true) {
        fail({
            "message": prependComment("Expected " + jsDump(value) + " to be a number", comment),
            "actual": value,
            "expected": Number
        });
    }
    return;
}

/**
 * Checks if the value passed as argument contains the pattern specified.
 * @param {String} value The string that should contain the pattern
 * @param {String} pattern The string that should be contained
 * @throws ArgumentsError
 * @throws AssertionError
 */
function stringContains(value, pattern) {
    var comment = evalArguments(arguments, arguments.callee.length);
    if (getType(pattern) === "string") {
        if (value.indexOf(pattern) < 0) {
            fail(prependComment("Expected string " + jsDump(pattern) +
                    " to be found in " + jsDump(value), comment));
        }
    } else {
        throw new ArgumentsError("Invalid argument to assertStringContains(string, string):\n" +
                             jsDump(pattern));
    }
    return;
}

/**
 * Checks if the regular expression matches the string.
 * @param {String} value The string that should contain the regular expression pattern
 * @param {RegExp} expr The regular expression that should match the value
 * @throws ArgumentsError
 * @throws AssertionError
 */
function matches(value, expr) {
    var comment = evalArguments(arguments, arguments.callee.length);
    if (getType(expr) === "regexp") {
        if (expr.test(value) == false) {
            fail(prependComment("Expected pattern " + jsDump(expr) + " to match " +
                    jsDump(value), comment));
        }
    } else {
        throw new ArgumentsError("Invalid argument to assertMatch(string, regexp):\n" +
                             jsDump(expr));
    }
    return;
}
