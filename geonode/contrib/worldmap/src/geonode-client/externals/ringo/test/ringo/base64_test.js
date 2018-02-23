var assert = require("assert");
var base64 = require('ringo/base64');
var {ByteString} = require('binary');

var data = [
    ["pleasure", "cGxlYXN1cmU="],
    ["leasure", "bGVhc3VyZQ=="],
    ["easure", "ZWFzdXJl"],
    ["asure", "YXN1cmU="],
    ["sure", "c3VyZQ=="],
    ["\u2665", "4pml"]
];

exports.testEncodeDecode = function () {
    for each (var test in data) {
        assert.strictEqual(base64.encode(test[0]), test[1]);
        assert.strictEqual(base64.decode(base64.encode(test[0])), test[0]);
        assert.deepEqual(base64.decode(
                base64.encode(test[0]), 'raw').toArray(),
                new ByteString(test[0], 'utf8').toArray());
    }
};
