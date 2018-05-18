var assert = require("assert");
include('ringo/encoding');
include('binary');
include('io');

var str = "I \u2665 JS";
var bytes = new ByteString([73,32,226,153,165,32,74,83]);

exports.testEncoder = function() {
    var enc = new Encoder("utf-8");
    enc.encode(str).encode(str);
    assert.strictEqual(str + str, enc.toByteString().decodeToString("utf-8"));
    enc.encode(str);
    assert.strictEqual(str + str + str, enc.toByteString().decodeToString("utf-8"));
    enc.clear().encode(str);
    assert.strictEqual(str, enc.toByteString().decodeToString("utf-8"));
};

exports.testSmallEncoder = function() {
    var enc = new Encoder("utf-8", false, 2);
    enc.encode(str).encode(str);
    assert.strictEqual(str + str, enc.toByteString().decodeToString("utf-8"));
    enc.encode(str);
    assert.strictEqual(str + str + str, enc.toByteString().decodeToString("utf-8"));
    enc.clear().encode(str);
    assert.strictEqual(str, enc.toByteString().decodeToString("utf-8"));
};

exports.testStreamEncoder = function() {
    var enc = new Encoder("utf-8");
    var stream = new MemoryStream();
    enc.writeTo(stream);
    enc.encode(str).encode(str);
    assert.strictEqual(enc.length, 0);
    assert.strictEqual(str + str, stream.content.decodeToString("utf-8"));
    enc.encode(str);
    assert.strictEqual(enc.length, 0);
    assert.strictEqual(str + str + str, stream.content.decodeToString("utf-8"));
    enc.clear().encode(str);
    assert.strictEqual(enc.length, 0);
    assert.strictEqual(str + str + str + str, stream.content.decodeToString("utf-8"));
};

exports.testDecoder = function() {
    var dec = new Decoder("utf-8");
    dec.decode(bytes).decode(bytes);
    assert.strictEqual(str + str, dec.toString());
    dec.decode(bytes);
    assert.strictEqual(str + str + str, dec.toString());
    dec.clear().decode(bytes);
    assert.strictEqual(str, dec.toString());
};

exports.testDecoderSmall = function() {
    var dec = new Decoder("utf-8", false, 2);
    dec.decode(bytes).decode(bytes);
    assert.strictEqual(str + str, dec.toString());
    dec.decode(bytes);
    assert.strictEqual(str + str + str, dec.toString());
    dec.clear().decode(bytes);
    assert.strictEqual(str, dec.toString());
};

exports.testStreamDecoder = function() {
    var dec = new Decoder("utf-8");
    var stream = new MemoryStream();
    stream.write(bytes.concat(bytes).concat(bytes));
    stream.position = 0;
    dec.readFrom(stream);
    assert.strictEqual(str + str + str, dec.read());
    assert.strictEqual(null, dec.read());
    assert.strictEqual(0, dec.length);
};

exports.testStreamDecoderReadLine = function() {
    var dec = new Decoder("utf-8");
    var stream = new MemoryStream();
    new TextStream(stream, {charset: "utf-8"}).writeLine(str).writeLine(str).writeLine(str);
    stream.position = 0;
    dec.readFrom(stream);
    assert.strictEqual(str, dec.readLine());
    assert.strictEqual(str, dec.readLine());
    assert.strictEqual(str, dec.readLine());
    assert.strictEqual(null, dec.readLine());
    assert.strictEqual(0, dec.length);
};

exports.testStreamDecoderReadLineShort = function() {
    var line = "The quick brown fox jumps over the lazy dog";
    var dec = new Decoder("utf-8", false, 2);
    var stream = new MemoryStream();
    new TextStream(stream, {charset: "utf-8"}).writeLine(line).writeLine(line).writeLine(line);
    stream.position = 0;
    dec.readFrom(stream);
    assert.strictEqual(line, dec.readLine());
    assert.strictEqual(line, dec.readLine());
    assert.strictEqual(line, dec.readLine());
    assert.strictEqual(null, dec.readLine());
    assert.strictEqual(0, dec.length);
};
