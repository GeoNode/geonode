var assert = require('assert');
include("binary");

exports.testByteArraySlice = function() {
    var a = [1, 2, 3, 4, 5, 6, 7, 8, 9, 0];
    var b = new ByteArray(a);
    var s = b.slice();
    assert.isTrue(s instanceof ByteArray);
    assert.strictEqual(10, s.length);
    assert.deepEqual(a, s.toArray());

    s = b.slice(3, 6);
    assert.isTrue(s instanceof ByteArray);
    assert.strictEqual(3, s.length);
    assert.deepEqual(a.slice(3, 6), s.toArray());

    s = b.slice(3, 4);
    assert.isTrue(s instanceof ByteArray);
    assert.strictEqual(1, s.length);
    assert.deepEqual(a.slice(3, 4), s.toArray());

    s = b.slice(3, 3);
    assert.isTrue(s instanceof ByteArray);
    assert.strictEqual(0, s.length);
    assert.deepEqual(a.slice(3, 3), s.toArray());

    s = b.slice(3, 2);
    assert.isTrue(s instanceof ByteArray);
    assert.strictEqual(0, s.length);
    assert.deepEqual(a.slice(3, 2), s.toArray());

    s = b.slice(7);
    assert.isTrue(s instanceof ByteArray);
    assert.strictEqual(3, s.length);
    assert.deepEqual(a.slice(7), s.toArray());

    s = b.slice(3, -2);
    assert.isTrue(s instanceof ByteArray);
    assert.strictEqual(5, s.length);
    assert.deepEqual(a.slice(3, -2), s.toArray());

    s = b.slice(-2);
    assert.isTrue(s instanceof ByteArray);
    assert.strictEqual(2, s.length);
    assert.deepEqual(a.slice(-2), s.toArray());

    s = b.slice(50);
    assert.isTrue(s instanceof ByteArray);
    assert.strictEqual(0, s.length);
    assert.deepEqual(a.slice(50), s.toArray());

    s = b.slice(-100, 100);
    assert.isTrue(s instanceof ByteArray);
    assert.strictEqual(10, s.length);
    assert.deepEqual(a.slice(-100, 100), s.toArray());

    s = b.slice("foo");
    assert.isTrue(s instanceof ByteArray);
    assert.strictEqual(10, s.length);
    assert.deepEqual(a.slice("foo"), s.toArray());

    s = b.slice("foo", "bar");
    assert.isTrue(s instanceof ByteArray);
    assert.strictEqual(0, s.length);
    assert.deepEqual(a.slice("foo", "bar"), s.toArray());
};

if (require.main === module.id) {
    run(exports);
}
