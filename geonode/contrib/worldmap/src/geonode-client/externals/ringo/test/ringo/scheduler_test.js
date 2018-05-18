var assert = require("assert");
include("ringo/scheduler");
var {Worker} = require("ringo/worker");
var {Semaphore} = require("ringo/concurrent");

exports.testSetTimeout = function() {
    var value;
    var semaphore = new Semaphore();
    // Spawn worker which will set timeout
    var worker = new Worker(module.id);
    worker.onmessage = function(e) {
        value = e.data;
    }
    worker.postMessage({test: 1, semaphore: semaphore}, true);
    // wait for promises to resolve
    if (!semaphore.tryWait(1000)) {
        assert.fail("timed out");
    }
    // make sure promises have resolved via chained callback
    assert.equal(value, "value");
    worker.terminate();
};

exports.testSetInterval = function() {
    var value = 0;
    var semaphore = new Semaphore();
    // Spawn worker which will set interval
    var worker = new Worker(module.id);
    worker.onmessage = function(e) {
        value += e.data;
    }
    worker.postMessage({test: 2, semaphore: semaphore}, true);
    // wait for promises to resolve
    if (!semaphore.tryWait(1000, 3)) {
        assert.fail("timed out");
    }
    // make sure promises have resolved via chained callback
    assert.equal(value, 30);
    worker.terminate();
};

// Worker onmessage handler
function onmessage(e) {
    if (e.data.test == 1) {
        setTimeout(function(arg) {
            e.source.postMessage(arg);
            e.data.semaphore.signal();
        }, 1, "value");
    } else {
        var id = setInterval(function(arg) {
            e.source.postMessage(arg);
            e.data.semaphore.signal();
        }, 5, 10);
    }
}

// start the test runner if we're called directly from command line
if (require.main == module.id) {
    system.exit(require('test').run(exports));
}
