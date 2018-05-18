var assert = require("assert");
var {EventEmitter} = require("ringo/events");

exports.testConstructor = function() {
    var e = new EventEmitter();
    assert.isTrue(e instanceof EventEmitter);
    testEmitter(e);
};

exports.testMixin = function() {
    var e = {};
    EventEmitter.call(e);
    assert.isFalse(e instanceof EventEmitter);
    testEmitter(e);
};

function testEmitter(e) {
    var count = 0;
    var add = function(amount) { count += amount };
    var subtract = function(amount) { count -= amount };
    var result;
    assert.equal(e.on, e.addListener, "on and addListener are different");
    e.addListener("add", add);
    e.addListener("addTwice", add).addListener("addTwice", add);
    assert.deepEqual(e.listeners("add"), [add]);
    assert.deepEqual(e.listeners("addTwice"), [add, add]);
    assert.deepEqual(e.listeners("subtract"), []);
    result = e.emit("add", 1);
    assert.equal(result, true);
    assert.equal(1, count);
    result = e.emit("subtract", 1);
    assert.equal(result, false);
    assert.equal(1, count);
    result = e.emit("addTwice", 1);
    assert.equal(result, true);
    assert.equal(3, count);
    e.addListener("addTwice", subtract).addListener("addTwice", add);
    assert.deepEqual(e.listeners("addTwice"), [add, add, subtract, add]);
    result = e.emit("addTwice", 1);
    assert.equal(result, true);
    assert.equal(5, count);
    e.removeListener("addTwice", subtract);
    assert.deepEqual(e.listeners("addTwice"), [add, add, add]);
    e.removeListener("addTwice", add);
    assert.deepEqual(e.listeners("addTwice"), [add, add]);
    result = e.emit("addTwice", 1);
    assert.equal(result, true);
    assert.equal(7, count);
    e.removeAllListeners("addTwice");
    assert.deepEqual(e.listeners("addTwice"), []);
    result = e.emit("addTwice", 1);
    assert.equal(result, false);
    assert.equal(7, count);
}