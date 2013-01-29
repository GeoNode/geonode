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
                testPassed = 0,
                current_test_assertions = [];

            QUnit.moduleStart = function (details) {
                moduleStart = new Date();
                module = details;
                testCases = []; // reset the testCase array
            };

            QUnit.testStart = function () {
                testStart = new Date();
            };


            QUnit.testDone = function (context) {
                var xml, i, l = current_test_assertions.length;

                if (0 === context.failed) {
                    testPassed += 1;
                } else {
                    testFailed += 1;
                }

                xml = '<testcase classname= "' + module.name + '"' +
                      'name="' + context.name + '"' +
                      'time="' + (new Date() - testStart) / 1000  + '"';


                if (context.failed) {
                    xml += '/>\n';
                    for (i = 0; i < l; i += 1) {
                        xml += current_test_assertions[i];
                    }
                    xml += '</testcase>\n';
                } else {
                    xml += '/>\n';
                }

                // reset the current_test_assertions after a test suite is done
                current_test_assertions = [];

                testCases.push(xml);
            };

            QUnit.moduleDone = function (context) {
                var i, l,
                    xml = '<testsuite ' +
                    'name="' + context.name +  '"' +
                    'errors="0" failures="' + context.failed +  '"' +
                    'tests="' + context.total + '"' +
                    'time="'  + (new Date() -  moduleStart) / 1000 + '  "';

                if (testCases.length) {
                    xml += '>\n';
                    for (i = 0, l = testCases.length; i < l; i += 1) {
                        xml += testCases[i];
                    }
                    xml += '</testsuite>\n\n';
                } else {
                    xml += '/>\n\n';
                }

                junitXml += xml;
            };


            QUnit.log = function (details) {
                var xml;

                console.log(
                    '{%s} (%s) [%s] %s',
                    module.name,
                    count += 1,
                    details.result ? 'PASSED' : 'FAILED',
                    details.message
                );
                // if the result if true then bail
                if (details.result) {
                    return;
                }

                xml = '<failure type="failed" message="' + details.message + '"/>';
                current_test_assertions.push(xml);
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

                // really java?
                bw = new java.io.BufferedWriter(new java.io.FileWriter(out.getAbsoluteFile()));
                bw.write(junitXml);
                bw.close();

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
