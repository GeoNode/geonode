var assert = require('assert');
var subprocess = require('ringo/subprocess');
var fs = require('fs');

const RINGO_HOME = system.prefix;

function isWindows() /win/i.test(java.lang.System.getProperty('os.name'));

exports.testCwdSensibleness = function () {
    fs.changeWorkingDirectory(RINGO_HOME);

    var cmd = isWindows() ? 'cmd /c cd' : '/bin/pwd';
    var out = subprocess.command(cmd)
            .replace(/\n/, '')
            .replace(/\\/g, '/');
    var pwd = /\/$/.test(out) ? out : out + '/';

    assert.strictEqual(fs.workingDirectory(), RINGO_HOME);
    assert.strictEqual(pwd, isWindows() ?
            RINGO_HOME.replace(/\\/g, '/') : RINGO_HOME);
};
