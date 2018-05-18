var assert = require("assert");
var fs = require('fs');
var separator = require('ringo/utils/files').separator;

var tests = [
    ['', ''],
    ['.', ''],
    ['./', ''],
    ['../', '../'],
    ['../a', '../a'],
    ['../a/', '../a/'],
    ['a/..', ''],
    ['a/../', ''],
    ['a/../b', 'b'],
    ['a/../b/', 'b/'],
];

tests.forEach(function([path, expected]) {
    exports['test "' + path + '"'] = function () {
        var result = fs.normal(localize(path));
        assert.strictEqual(localize(expected), result);
    };
});

// adapt path to the platform we're running on
function localize(path) {
    return path.replace(/\//g, separator);
}

if (require.main === module.id) {
    run(exports);
}