var assert = require("assert");
var fs = require('fs');
var {separator, roots} = require('ringo/utils/files');

var tests = [
    [['/'], '/'],
    [['/a'], '/a'],
    [['/a/'], '/a/'],
    [['/a', '/b'], '/b'],
    [['/a', '/b/'], '/b/'],
    [['/', 'a'], '/a'],
    [['/', 'a/'], '/a/'],
    [['/a', 'a'], '/a'],
    [['/a', 'a/'], '/a/'],
    [['/a/', 'a'], '/a/a'],
    [['/a/', 'a/'], '/a/a/'],
    [['..'], '../'],
    [['..', 'a'], '../a'],
    [['..', 'a/'], '../a/'],
    [['.'], ''],
    [['.', 'a'], 'a'],
    [['.', 'a/'], 'a/'],
    [['a', '.'], ''],
    [['a', '.', 'a'], 'a'],
    [['a', '.', 'a/'], 'a/'],
    [['a', '..'], '../'],
    [['a', '..', 'a'], '../a'],
    [['a', '..', 'a/'], '../a/'],
    [['a/', '..'], ''],
    [['a/', '..', 'a'], 'a'],
    [['a/', '..', 'a/'], 'a/'],
    [['a/b', ''], 'a/b'],
];

tests.forEach(function([parts, expected]) {
    exports['test ' + parts.toSource()] = function () {
        var result = fs.resolve.apply(null, parts.map(localize));
        assert.strictEqual(localize(expected), result);
    };
});

// adapt path to the platform we're running on
function localize(path) {
    return path.replace(/^\//, roots[0]).replace(/\//g, separator);
}

if (require.main === module.id) {
    run(exports);
}

