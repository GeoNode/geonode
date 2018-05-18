
include('ringo/engine');
var assert = require('assert');
var fs = require('fs');

[
    'absolute',
    'cyclic',
    'exactExports',
    'hasOwnProperty',
    'method',
    'missing',
    'monkeys',
    'nested',
    'reflexive',
    'relative',
    'transitive',
    'determinism'
].forEach(function (testName) {
    exports['test ' + testName] = function () {
        var prefix = fs.resolve(module.path, testName);
        var done;

        var print = function (message) {
            assert.isFalse(/^FAIL/.test(message));
            if (/^ERROR/.test(message))
                throw new Error(message);
            if (/^DONE/.test(message))
                done = true;
        };

        var sys = Object.create(system, {
            print: { value: print }
        });

        var sandbox = createSandbox(
            [prefix], // module path
            {sys: sys}, // globals
            {systemModules: ["modules"]} // options
        );

        sandbox.runScript('program.js');
        assert.isTrue(done, 'done');
    };
});

if (module.id == require.main) {
    run(exports);
}