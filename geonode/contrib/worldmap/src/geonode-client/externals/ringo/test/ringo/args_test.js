var assert = require("assert");
var Parser = require('ringo/args').Parser;

exports.setUp = exports.tearDown = function() {}

exports.testBasic = function () {
    var p = new Parser();
    p.addOption("q", null, null, "Be quiet about errors and warnings");
    p.addOption("s", "silent", null, "Ignore errors and warnings");
    p.addOption("c", "counter", "NUMBER", "Init counter with NUMBER");
    assert.deepEqual({silent: true}, p.parse(['-s']));
    assert.deepEqual({silent: true}, p.parse(['--silent']));
    assert.deepEqual({q: true}, p.parse(['-q']));
    assert.deepEqual({counter: "42"}, p.parse(['-c', '42']));
    assert.deepEqual({counter: "42"}, p.parse(['-c42']));
    assert.deepEqual({counter: "42"}, p.parse(['--counter=42']));
    assert.deepEqual({counter: "42"}, p.parse(['--counter', '42']));
    assert.deepEqual({counter: "42", silent: true, q: true}, p.parse(['-sqc42']));
    assert.deepEqual({counter: "42", silent: true, q: true}, p.parse(['-sqc', '42']));
    // missing option argument
    assert.throws(function() {p.parse(['--counter']);});
    assert.throws(function() {p.parse(['-c']);});
    assert.throws(function() {p.parse(['-sqc']);});
    // unknown option
    assert.throws(function() {p.parse(['--unknown']);});
    assert.throws(function() {p.parse(['-u']);});
    assert.throws(function() {p.parse(['-squ']);});
}
