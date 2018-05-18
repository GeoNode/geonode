var {AsyncResponse} = require('ringo/jsgi/connector');
var {setInterval, clearInterval} = require('ringo/scheduler');

exports.app = function(request) {
    var response = new AsyncResponse(request, 30000, true);
    response.start(200, {'Content-Type': 'text/plain'});
    // Keep writing to the client until we catch an error.
    var i = setInterval(function() {
        try {
            print("writing");
            response.write('hello\n');
        } catch (e) {
            print("error: " + e);
            clearInterval(i);
        }
    }, 1000);
    return response;
}

if (require.main === module) {
    require('ringo/httpserver').main(module.id);
}
