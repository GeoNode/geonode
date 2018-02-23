var {Worker} = require("ringo/worker");
var {Semaphore} = require("ringo/concurrent");
var {setTimeout} = require("ringo/scheduler");

function main() {
    // Create a semaphore to wait for response from all workers
    var s = new Semaphore();
    var NUMBER_OF_WORKERS = 8;
    
    // Create a new workers from this same module. Note that this will
    // create a new instance of this module as workers are isolated.
    for (var i = 0; i < NUMBER_OF_WORKERS; i++) {
        var w = new Worker(module.id);
        w.onmessage = function(e) {
            print("Got reply from worker " + e.data);
            s.signal();
        }
        // Calling worker.postMessage with true as second argument causes
        // callbacks from the worker to be executed synchronously in
        // the worker's own thread instead of in our own event loop thread,
        // allowing us to wait synchronously for replies.
        w.postMessage(i, true);
    }
    
    // Wait until we have responses from all workers, but with
    // a timeout that is barely long enough.
    if (s.tryWait(800, NUMBER_OF_WORKERS)) {
        print("Got responses from all workers, quitting.");
    } else {
        print("Timed out; quitting.");
    }
}

function onmessage(e) {
    print("Starting worker " + e.data);
    // Respond with a timeout depending on the input data we got
    setTimeout(function() {
        e.source.postMessage(e.data);
    }, e.data * 100);
}

if (require.main === module) {
    main();
}

