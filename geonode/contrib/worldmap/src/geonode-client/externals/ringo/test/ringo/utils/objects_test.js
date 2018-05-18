var assert = require('assert');
var objects = require('ringo/utils/objects');

exports.testMerge = function() {
    var x = {a: 1, b: 2};
    var y = {b: 3, c: 4};
    var z = {c: 5, d: 6};

    // degenerate zero/single-argument cases
    assert.deepEqual(objects.merge(),          {});
    assert.deepEqual(objects.merge(x),         {a: 1, b: 2});

    // property values of "earlier" arguments are promoted into the result
    assert.deepEqual(objects.merge(x, y),      {a: 1, b: 2, c: 4});
    assert.deepEqual(objects.merge(y, x),      {b: 3, c: 4, a: 1});

    assert.deepEqual(objects.merge(x, y, z),   {a: 1, b: 2, c: 4, d: 6});
    assert.deepEqual(objects.merge(y, z, x),   {b: 3, c: 4, d: 6, a: 1});
    assert.deepEqual(objects.merge(z, x, y),   {c: 5, d: 6, a: 1, b: 2});

    // check that the objects passed as arguments were not modified
    assert.deepEqual(x,                       {a: 1, b: 2});
    assert.deepEqual(y,                       {b: 3, c: 4});
    assert.deepEqual(z,                       {c: 5, d: 6});
};
