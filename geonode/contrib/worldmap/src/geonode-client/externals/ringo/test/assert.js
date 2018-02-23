var assert = require("assert");
var jsDump = require("test").jsDump;

var getFunction = function(func) {
    var args = Array.prototype.slice.call(arguments, 1);
    return function() {
        func.apply(this, args);
    };
};



/***************************************************************
 *****   C O M M O N J S   A S S E R T I O N   T E S T S   *****
 ***************************************************************/



exports.testOk = function() {
    assert.ok(true);
    assert.ok("1");
    assert.ok([]);
    assert.ok({});
    assert.ok(new Boolean(false));
    assert.ok(Infinity);
    assert.throws(getFunction(assert.ok, 0), assert.AssertionError);
    assert.throws(getFunction(assert.ok, false), assert.AssertionError);
    assert.throws(getFunction(assert.ok, null), assert.AssertionError);
    assert.throws(getFunction(assert.ok, undefined), assert.AssertionError);
};

exports.testEqual = function() {
    assert.equal(true, true);
    assert.equal(true, "1");
    assert.equal(false, false);
    assert.equal(false, "");
    assert.equal(false, "0");
    assert.equal(null, undefined);
    assert.throws(getFunction(assert.equal, true, false), assert.AssertionError);
    assert.throws(getFunction(assert.equal, "", true), assert.AssertionError);
};

exports.testNotEqual = function() {
    assert.notEqual(true, false);
    assert.notEqual(1, 2);
    assert.notEqual("one", "eno");
    assert.notEqual(false, NaN);
    assert.notEqual(null, NaN);
    assert.notEqual(undefined, NaN);
    assert.notEqual([], []);
    assert.notEqual({}, {});
    assert.throws(getFunction(assert.notEqual, "", false), assert.AssertionError);
    assert.throws(getFunction(assert.notEqual, "0", false), assert.AssertionError);
    assert.notEqual(/^test.*/gim, /^test.*/gim);
    var date1 = new Date(2009, 5, 6, 12, 31, 27);
    var date2 = new Date(date1.getTime());
    assert.notEqual(date1, date2);
    // functions
    var func1 = function() {
        var x = 0;
        x += 1;
        return;
    };
    var func2 = function() {
        var x = 0;
        x += 1;
        return;
    };
    assert.notEqual(func1, func2);
    return;
};

exports.testDeepEqual = function() {
    // 7.1
    assert.deepEqual(true, true);
    assert.deepEqual(1, 1);
    assert.deepEqual("one", "one");
    assert.deepEqual("", "");
    assert.deepEqual(null, undefined);
    // 7.2
    assert.deepEqual(new Date(2010, 5, 14), new Date(2010, 5, 14));
    // 7.3
    assert.deepEqual(5, "5");
    assert.deepEqual("5", 5);
    assert.deepEqual(true, 1);
    assert.deepEqual(null, undefined);
    // 7.4
    assert.deepEqual({"one": 1}, {"one": 1});
    assert.deepEqual({"one": 1, "two": "2"}, {"one": 1, "two": "2"});
    assert.deepEqual([""], [""]);
    assert.deepEqual([1], ["1"]);
    // FIXME (ro): this is from narwhal, i doubt this makes sense
    // assert.deepEqual(["one"], {0: "one"});
    // instead this implementation throws an exception due to different prototypes
    assert.throws(getFunction(assert.deepEqual, ["one"], {0: "one"}), assert.AssertionError);
    assert.deepEqual({"one": 1, "two": "2"}, {"two": "2", "one": 1});
    assert.deepEqual({
        "foo": [1],
        "bar": [["1"], [2, null]]
    }, {
        "foo": [1],
        "bar": [["1"], [2, null]]
    });
    assert.deepEqual({
        "foo": {
            "one": "1"
        },
        "bar": {
            "two": {
                "three": "3",
                "bool": false
            }
        }
    }, {
        "foo": {
        "one": "1"
        },
        "bar": {
            "two": {
                "three": "3",
                "bool": false
            }
        }
    });

    // array with named properties
    var arr1 = [1, 2, 3, 4, 5];
    var arr2 = [1, 2, 3, 4, 5];
    arr1.name = "test";
    arr1.isValid = true;
    arr2.isValid = true;
    arr2.name = "test";
    assert.deepEqual(arr1, arr2);
    arr2.name = "other";
    assert.throws(getFunction(assert.deepEqual, arr1, arr2), assert.AssertionError);

    // same prototype
    var Base = function() {
        this.type = "Base";
        return this;
    };

    var Foo = function(name) {
        this.name = name;
        return this;
    };
    Foo.prototype = new Base();

    var Bar = function(name) {
        this.name = name;
        return this;
    }
    Bar.prototype = new Base();

    assert.deepEqual(new Foo("test"), new Foo("test"));
    assert.throws(getFunction(assert.deepEqual, new Foo("test"), new Bar("test")),
            assert.AssertionError);

    return;
};

exports.testNotDeepEqual = function() {
    // 7.1
    assert.notDeepEqual(1, "2");
    // 7.2
    assert.notDeepEqual(new Date(2010, 5, 14), new Date());
    // 7.4
    assert.notDeepEqual({
        "one": 1,
        "two": "2"
    }, {
        "one": 1
    });
    assert.notDeepEqual([1, 2], [1]);

    // named properties on array instances
    var arr1 = [1, 2, 3, 4, 5];
    var arr2 = [1, 2, 3, 4, 5];
    arr1.name = "test";
    arr2.name = "other";
    assert.notDeepEqual(arr1, arr2);

    // different prototypes
    var Foo = function(name) {
        this.name = name;
        return this;
    };
    Foo.prototype = {
        "type": "custom"
    };
    var Bar = function(name) {
        this.name = name;
        return this;
    };
    var obj1 = new Foo("test");
    var obj2 = new Bar("test");
    assert.notDeepEqual(new Foo("test"), new Bar("test"));
    // equal prototypes
    Bar.prototype = Foo.prototype;
    assert.throws(getFunction(assert.notDeepEqual, new Foo("test"), new Bar("test")),
            assert.assertionError);
    return;
};

exports.testStrictEqual = function() {
    assert.strictEqual(null, null);
    assert.strictEqual(undefined, undefined);
    assert.strictEqual(1, 1);
    assert.strictEqual("1", "1");
    assert.strictEqual(true, true);
    var obj = {};
    assert.strictEqual(obj, obj);
    var arr = [];
    assert.strictEqual(arr, arr);
    assert.strictEqual(Infinity, Infinity);
    assert.throws(getFunction(assert.strictEqual, null, undefined), assert.AssertionError);
    return;
};

exports.testNotStrictEqual = function() {
    assert.notStrictEqual(null, undefined);
    assert.notStrictEqual(1, "1");
    assert.notStrictEqual(true, false);
    assert.notStrictEqual({}, {});
    assert.notStrictEqual([], []);
    assert.notStrictEqual(NaN, NaN);
    assert.throws(getFunction(assert.notStrictEqual, null, null), assert.AssertionError);
    return;
};

exports.testThrows = function() {
    // throw undefined (yes, you can do that...)
    assert.throws(function() {
        throw undefined;
    }, undefined);
    // throw Error instance
    assert.throws(function() {
        throw new Error("a message");
    }, Error);
    // throw AssertionError (extends Error)
    assert.throws(function() {
        throw new assert.AssertionError();
    }, assert.AssertionError);
    // throw string
    assert.throws(function() {
        throw "my message";
    }, "my message");
    // throw java exception
    assert.throws(function() {
        var x = new java.util.Vector(0);
        x.get(1);
    }, java.lang.ArrayIndexOutOfBoundsException);
    // throw anything, but don't check further
    assert.throws(function() {
        throw new Date();
    });
    assert.throws(function() {
        assert.throws(function() {
            throw new assert.ArgumentsError("test");
        }, assert.AssertionError)
    }, assert.AssertionError);
    return;
};



/***********************************************************
 *****   C U S T O M   A S S E R T I O N   T E S T S   *****
 ***********************************************************/



exports.testIsTrue = function() {
    assert.isTrue(true);
    assert.throws(getFunction(assert.isTrue, false), assert.AssertionError);
    return;
};

exports.testIsFalse = function() {
    assert.isFalse(false);
    assert.throws(getFunction(assert.isFalse, true), assert.AssertionError);
    return;
};

exports.testIsNull = function() {
    assert.isNull(null);
    assert.throws(getFunction(assert.isNull, undefined), assert.AssertionError);
    return;
};

exports.testIsNotNull = function() {
    assert.isNotNull(0);
    assert.isNotNull("");
    assert.isNotNull(undefined);
    assert.isNotNull("0");
    assert.throws(getFunction(assert.isNotNull, null), assert.AssertionError);
    return;
};

exports.testIsUndefined = function() {
    assert.isUndefined(undefined);
    assert.throws(getFunction(assert.isUndefined, null), assert.AssertionError);
    return;
};

exports.testIsNotUndefined = function() {
    assert.isNotUndefined(null);
    assert.throws(getFunction(assert.isNotUndefined, undefined), assert.AssertionError);
    return;
};

exports.testIsNaN = function() {
    assert.isNaN("a");
    assert.throws(getFunction(assert.isNaN, 123), assert.AssertionError);
    return;
};

exports.testIsNotNaN = function() {
    assert.isNotNaN(1);
    assert.throws(getFunction(assert.isNotNaN, NaN), assert.AssertionError);
    return;
};

exports.testStringContains = function() {
    assert.stringContains("just a test", "test");
    assert.throws(getFunction(assert.stringContains, "just a test", "foo"), assert.AssertionError);
    return;
};

exports.testMatches = function() {
    assert.matches("just a test", /t.?st/);
    assert.throws(getFunction(assert.matches, "just a test", /foo/), assert.AssertionError);
    return;
};



/***************************************
 *****   J S D U M P   T E S T S   *****
 ***************************************/



exports.testDumpObject = function() {
    assert.strictEqual(
        jsDump({
            "a": 1,
            "b": {
                "c": 2
            },
            "e": 23
        }),
        [
            '{',
            '    "a": 1,',
            '    "b": {',
            '        "c": 2',
            '    },',
            '    "e": 23',
            '}'
        ].join("\n")
    );
    return;
};

exports.testDumpSimpleArray = function() {
    assert.strictEqual(
        jsDump([0, "eins", 2, 3]),
        [
            '[',
            '    0,',
            '    "eins",',
            '    2,',
            '    3',
            ']'
        ].join("\n")
    );
    return;
};

exports.testDumpMultiDimensionalArray = function() {
    assert.strictEqual(
        jsDump([0, "eins", ["a", ["one", "two"], "c"], 3]),
        [
            '[',
            '    0,',
            '    "eins",',
            '    [',
            '        "a",',
            '        [',
            '            "one",',
            '            "two"',
            '        ],',
            '        "c"',
            '    ],',
            '    3',
            ']'
        ].join("\n")
    );
    return;
};

exports.testDumpMixedArray = function() {
    assert.strictEqual(
        jsDump([0, "eins", ["a", {"a": 0, "b": {"c": 3}, "d": 4}, "c"], 3]),
        [
            '[',
            '    0,',
            '    "eins",',
            '    [',
            '        "a",',
            '        {',
            '            "a": 0,',
            '            "b": {',
            '                "c": 3',
            '            },',
            '            "d": 4',
            '        },',
            '        "c"',
            '    ],',
            '    3',
            ']'
        ].join("\n")
    );
    return;
};

exports.testDumpString = function() {
    assert.strictEqual(jsDump("one"), '"one"');
    assert.strictEqual(jsDump("0"), '"0"');
    return;
};

exports.testDumpNumber = function() {
    assert.strictEqual(jsDump(12), "12");
    assert.strictEqual(jsDump(Infinity), "Infinity");
    return;
};

exports.testDumpNaN = function() {
    assert.strictEqual(jsDump(NaN), "NaN");
    return;
};

exports.testDumpBoolean = function() {
    assert.strictEqual(jsDump(true), "true");
    return;
};

exports.testDumpDate = function() {
    var d = new Date();
    assert.strictEqual(jsDump(d), d.toString());
    return;
};

exports.testDumpRegExp = function() {
    var re = /^test(.*)/gim;
    assert.strictEqual(jsDump(re), "/^test(.*)/gim");
    return;
};

exports.testDumpFunction = function() {
    assert.equal(jsDump(exports.testDumpObject), exports.testDumpObject.toSource());
    return;
};
