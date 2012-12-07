/*global window: true, Envjs:true, load:true, QUnit */
load("libs/env-js/dist/env.rhino.js");

Envjs({
    scriptTypes: {
        'text/javascript': true
    },
    afterScriptLoad: {
        '.*': function (scriptNode) {

            // trigger script load event
            var event = document.createEvent('Event');
            event.initEvent('load', true, true);
            scriptNode.dispatchEvent(event);
        },

        'qunit': function (script) {
            var count = 0,
                module;
            QUnit.moduleStart = function (details) {
                module = details;
            };
            QUnit.log = function (details) {
                console.log(
                    '{%s} (%s) [%s] %s',
                    module.name,
                    count++,
                    details.result ? 'PASSED' : 'FAILED',
                    details.message
                );
            };

        }


    }
});

var specFile, i;

for (i = 0; i < arguments.length; i += 1) {

    specFile = arguments[i];
    console.log("Loading: " + specFile);
    window.location = specFile;

}
