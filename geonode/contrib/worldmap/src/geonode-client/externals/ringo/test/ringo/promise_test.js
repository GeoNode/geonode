var assert = require("assert");
var {Deferred, PromiseList} = require("ringo/promise");
var {Semaphore} = require("ringo/concurrent");

exports.testPromise = function() {
    var d1 = new Deferred(), d2 = new Deferred();
    var semaphore = new Semaphore();
    var v1, v2, e2;
    d1.promise.then(function(value) {
        v1 = value;
        semaphore.signal();
    });
    d2.promise.then(function(value) {
        v2 = value;
    }, function(error) {
        e2 = error;
        semaphore.signal();
    });
    // Resolve promise in thread so async promise callbacks get called
    spawn(function() {
        d1.resolve("value");
        d2.resolve("error", true);
    });
    // wait for promises to resolve
    if (!semaphore.tryWait(1000, 2)) {
        assert.fail("timed out");
    }
    // make sure promises have resolved via chained callback
    assert.equal(v1, "value");
    assert.equal(v2, undefined);
    assert.equal(e2, "error");
};

exports.testPromiseList = function() {
    var d1 = Deferred(), d2 = Deferred(), d3 = Deferred(), done = Deferred();
    var l = PromiseList(d1.promise, d2.promise, d3); // PromiseList should convert d3 to promise
    var semaphore = new Semaphore();
    var result;
    l.then(function(value) {
        done.resolve(value);
    }, function(error) {
        done.resolve("promises called error callback", true);
    });
    done.promise.then(function(value) {
        result = value;
        semaphore.signal();
    });
    // Resolve promises in thread so async promise callbacks get called
    spawn(function() {
        d2.resolve(1);
        d3.resolve("error", true);
        d1.resolve("ok");
    });
    // wait for last promise to resolve
    if (!semaphore.tryWait(1000)) {
        assert.fail("timed out");
    }
    // make sure promises have resolved via chained callback
    assert.deepEqual(result, [{value: "ok"}, {value: 1}, {error: "error"}]);
};

// start the test runner if we're called directly from command line
if (require.main == module.id) {
    system.exit(require('test').run(exports));
}
