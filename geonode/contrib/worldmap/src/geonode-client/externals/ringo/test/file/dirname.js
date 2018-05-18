var assert = require('assert');
var fs = require('fs');

var tests = [
    ['', '.'],
    ['.', '.'],
    ['foo', '.'],
    //['foo/', '.'],
    ['foo/bar', 'foo']
    // TODO: many more tests
];

tests.forEach(function ([path, expected]) {
    exports['test "' + path + '"'] = function () {
        var actual = fs.directory(path);
        assert.strictEqual(expected, actual);
    };
});

if (require.main === module.id) {
    run(exports);
}