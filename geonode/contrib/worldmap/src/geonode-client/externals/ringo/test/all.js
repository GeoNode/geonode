// Run complete RingoJS test suite.

// Unless your tests take a long time to run, consume lots of resources,
// or mess with global settings you probably should add them to ./most.js

// Include tests exported by most.js
var most = require('./most');
for (var key in most) {
    exports[key] = most[key];
}

// Add tests exclusive to all.js
exports.testHttpclient = require('./ringo/httpclient_test');

// start the test runner if we're called directly from command line
if (require.main == module.id) {
    system.exit(require('test').run(exports));
}
