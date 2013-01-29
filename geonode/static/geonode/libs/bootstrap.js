/*global window: true, java: true, Envjs:true, load:true, QUnit: true, document:true */
'use strict';

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
                junitXml = '',
                module,
                moduleStart,
                testStart,
                testCases = [],
                testFailed = 0,
                testPassed = 0;

            QUnit.moduleStart = function (details) {
                moduleStart = new Date();
                module = details;
            };

            QUnit.testStart = function () {
                testStart = new Date();
            };

            QUnit.done = function (details) {
                var out = new java.io.File('junit.xml'), bw;

                console.log('\n');
                console.log(testPassed + ' tests passed');
                console.log(testFailed + ' tests failed');
                console.log('\n');

                if (!out.exists()) {
                    out.createNewFile();
                }

                bw = new java.io.BufferedWriter(new java.io.FileWriter(out.getAbsoluteFile()));
                bw.write('test');

                bw.close();

            };


            QUnit.testDone = function (result) {
                if (0 === result.failed) {
                    testPassed += 1;
                } else {
                    testFailed += 1;
                }
            };


            QUnit.log = function (details) {
                console.log(
                    '{%s} (%s) [%s] %s',
                    module.name,
                    count += 1,
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
