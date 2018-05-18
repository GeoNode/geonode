include('io');
var {ByteString} = require('binary');
var assert = require('assert');

exports.testReadFixed = function() {
    var resource = getResource('./io_test.js');
    var io = new Stream(resource.inputStream);
    var bytes = io.read(7);
    assert.strictEqual(bytes.length, 7);
    assert.strictEqual(bytes.decodeToString(), 'include');
};

exports.testReadIndefinite = function() {
    var resource = getResource('./assert.js');
    var io = new Stream(resource.inputStream);
    var bytes = io.read();
    assert.strictEqual(bytes.length, resource.length);
    assert.strictEqual(bytes.decodeToString(), resource.content);
};

exports.testStreamForEach = function() {
    var resource = getResource('./assert.js');
    var io = new Stream(resource.inputStream);
    var str = '';
    var read = 0;
    io.forEach(function(data) {
        read += data.length;
        str += data.decodeToString();
    });
    assert.strictEqual(read, resource.length);
    assert.strictEqual(str, resource.content);
};

exports.testMemoryStream = function() {
    var m = new MemoryStream(20);
    var line = 'Lorem ipsum dolor sit amet, eam suas agam phaedrum an, cetero ' +
               'apeirian id vix, menandri evertitur eu cum.';
    var bytes = line.toByteString();
    for (var i = 0; i < 100; i++) {
        m.write(bytes);
    }
    assert.equal(m.length, bytes.length * 100);
    assert.equal(m.position, bytes.length * 100);
    m.position = 0;
    for (var j = 0; j < 100; j++) {
        assert.deepEqual(m.read(bytes.length), bytes);
    }
    assert.deepEqual(m.read(bytes.length), new ByteString());
}
