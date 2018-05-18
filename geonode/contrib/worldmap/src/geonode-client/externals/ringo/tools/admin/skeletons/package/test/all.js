var assert = require('assert');
var changeMe = require('skeleton');

exports.testSomething = function () {
    assert.ok(true);
};

if (require.main == module) {
    system.exit(require('test').run(exports));
}
