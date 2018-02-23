var assert = require("assert");
include("binary");

exports.testByteStringConstructorEncodings = function() {
    // ByteString(string, charset)
    // Convert a string. The ByteString will contain string encoded with charset.
    var testString = "hello world";
    var b4 = new ByteString(testString, "US-ASCII");
    assert.strictEqual(testString.length, b4.length);
    b4.length = 123;
    assert.strictEqual(testString.length, b4.length);
    assert.strictEqual(testString.charCodeAt(0), b4.get(0));
    assert.strictEqual(testString.charCodeAt(testString.length-1), b4.get(testString.length-1));
};

exports.testToByteArrayEncodings = function() {
    var testString = "I ♥ JS";
    assert.strictEqual(testString, new ByteString(testString, "UTF-8").toByteArray("UTF-8", "UTF-16").decodeToString("UTF-16"));
};

exports.testToByteStringEncodings = function() {
    var testString = "I ♥ JS";
    assert.strictEqual(testString, new ByteString(testString, "UTF-8").toByteString("UTF-8", "UTF-16").decodeToString("UTF-16"));
};

exports.testToArrayEncodings = function() {
    var a1;

    a1 = new ByteString("\u0024\u00A2\u20AC", "UTF-8").toArray("UTF-8");
    assert.strictEqual(3, a1.length);
    assert.strictEqual(0x24, a1[0]);
    assert.strictEqual(0xA2, a1[1]);
    assert.strictEqual(0x20AC, a1[2]);

    a1 = new ByteString("\u0024\u00A2\u20AC", "UTF-16").toArray("UTF-16");
    assert.strictEqual(3, a1.length);
    assert.strictEqual(0x24, a1[0]);
    assert.strictEqual(0xA2, a1[1]);
    assert.strictEqual(0x20AC, a1[2]);
};

exports.testDecodeToString = function() {
    assert.strictEqual("hello world", new ByteString("hello world", "US-ASCII").decodeToString("US-ASCII"));

    assert.strictEqual("I ♥ JS", new ByteString("I ♥ JS", "UTF-8").decodeToString("UTF-8"));

    assert.strictEqual("\u0024", new ByteString([0x24]).decodeToString("UTF-8"));
    assert.strictEqual("\u00A2", new ByteString([0xC2,0xA2]).decodeToString("UTF-8"));
    assert.strictEqual("\u20AC", new ByteString([0xE2,0x82,0xAC]).decodeToString("UTF-8"));
    // FIXME:
    //assert.strictEqual("\u10ABCD", (new ByteString([0xF4,0x8A,0xAF,0x8D])).decodeToString("UTF-8"));

    assert.strictEqual("\u0024", new ByteString("\u0024", "UTF-8").decodeToString("UTF-8"));
    assert.strictEqual("\u00A2", new ByteString("\u00A2", "UTF-8").decodeToString("UTF-8"));
    assert.strictEqual("\u20AC", new ByteString("\u20AC", "UTF-8").decodeToString("UTF-8"));
    assert.strictEqual("\u10ABCD", new ByteString("\u10ABCD", "UTF-8").decodeToString("UTF-8"));

    assert.strictEqual("\u0024", new ByteString("\u0024", "UTF-16").decodeToString("UTF-16"));
    assert.strictEqual("\u00A2", new ByteString("\u00A2", "UTF-16").decodeToString("UTF-16"));
    assert.strictEqual("\u20AC", new ByteString("\u20AC", "UTF-16").decodeToString("UTF-16"));
    assert.strictEqual("\u10ABCD", new ByteString("\u10ABCD", "UTF-16").decodeToString("UTF-16"));
};

exports.testStringToByteString = function() {
    assert.strictEqual("hello world", "hello world".toByteString("US-ASCII").decodeToString("US-ASCII"));
    assert.strictEqual("I ♥ JS", "I ♥ JS".toByteString("UTF-8").decodeToString("UTF-8"));
};

if (require.main === module.id) {
    run(exports);
}
