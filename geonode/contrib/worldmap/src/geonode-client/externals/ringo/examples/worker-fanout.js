var {Worker} = require("ringo/worker");

function main() {
    // Create a new workers from this same module. Note that this will
    // create a new instance of this module as workers are isolated.
    for (var i = 0; i < 8; i++) {
        var w = new Worker(module.id);
        w.onmessage = function(e) {
            print("Got reply from worker " + e.data);
        }
        w.postMessage(i);
    }
}

function onmessage(e) {
    print("Starting worker " + e.data);
    e.source.postMessage(e.data);
}

if (require.main === module) {
    main();
}

