var assert = require("assert");
var http = require("ringo/utils/http");

exports.testUrlEncode = function() {
    var encoded, expected;
    encoded = http.urlEncode({foo: 1, bar: "baz"});
    expected = "foo=1&bar=baz";
    assert.strictEqual(encoded, expected);
    encoded = http.urlEncode({foo: [1, 2, 3, 4, 5], bar: "baz"});
    expected = "foo=1&foo=2&foo=3&foo=4&foo=5&bar=baz";
    assert.strictEqual(encoded, expected);
};