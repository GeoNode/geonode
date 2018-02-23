var assert = require("assert");
var fs = require('fs');
var {separator} = require('ringo/utils/files');

var tests = [
    ['', '', ''],
    ['.', '', ''],
    ['', '.', ''],
    ['.', '.', ''],
    ['', '..', '../'],
    ['', '../', '../'],
    ['a', 'b', 'b'],
    ['../a', '../b', 'b'],
    ['../a/b', '../a/c', 'c'],
    ['a/b', '..', '../../'],
    ['a/b', 'c', '../c'],
    ['a/b', 'c/d', '../c/d'],
];

tests.forEach(function ([source, target, expected]) {
    var name = '"' + source + '" -> "' + target + '" = "' + expected + '"';
    exports['test ' + name] = function () {
        var actual = fs.relative(source, target);
        // expect returned paths to use system-dependent file separator
        assert.strictEqual(expected.replace(/\//g, separator), actual);
    };
});

if (require.main === module.id) {
    run(exports);
}