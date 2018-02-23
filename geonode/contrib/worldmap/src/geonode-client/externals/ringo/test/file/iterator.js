var assert = require("assert");
var fs = require("fs");

/* a decorator that passes a path object corresponding
   to the test name and removes any files created
   therein afterward */
var Test = function (block) {
    var exported = function () {
        for (var name in exports) {
            if (exports[name] === exported) {
                try {
                    var path = fs.path(
                        fs.resolve(module.path, '.'),
                        name
                    );
                    block(path);
                } finally {
                    if (path.exists())
                        path.removeTree();
                }
            }
        }
    };
    return exported;
};

exports.testPrintReadLine = Test(function (path) {
    var stream = path.open('w');
    stream.print('hello');
    stream.print('world');
    stream.close();
    stream = path.open('r');
    assert.strictEqual('hello\n', stream.readLine());
    assert.strictEqual('world\n', stream.readLine());
    assert.strictEqual('', stream.readLine());
    stream.close();
});

exports.testPrintReadLineChain = Test(function (path) {
    var stream = path.open('w');
    stream.print('hello').print('world');
    stream.close();
    stream = path.open('r');
    assert.strictEqual('hello\n', stream.readLine());
    assert.strictEqual('world\n', stream.readLine());
    assert.strictEqual('', stream.readLine());
    stream.close();
});

exports.testReadLines = Test(function (path) {
    var stream = path.open('w');
    stream.print('hello').print('world');
    stream.close();
    stream = path.open('r');
    assert.deepEqual(['hello\n', 'world\n'], stream.readLines());
    stream.close();
});

exports.testForEach = Test(function (path) {
    var output = path.open('w');
    var input = path.open('r');
    output.print('1');
    output.print('1');
    var count = 0;
    input.forEach(function (line) {
        assert.strictEqual('1', line);
        count++;
    });
    assert.strictEqual(2, count);
    output.print('2').print('2');
    input.forEach(function (line) {
        assert.strictEqual('2', line);
        count++;
    });
    assert.strictEqual(4, count);
    output.close();
    input.close();
});

exports.testNext = Test(function (path) {
    path.open('w').print('1').print('2').close();
    var iterator = path.open();
    assert.strictEqual('1', iterator.next());
    assert.strictEqual('2', iterator.next());
    assert.throws(function () {
        iterator.next();
    });
    iterator.close();
});

exports.testIterator = Test(function (path) {
    path.open('w').print('1').print('2').close();
    var iterator = path.open().iterator();
    assert.strictEqual('1', iterator.next());
    assert.strictEqual('2', iterator.next());
    assert.throws(function () {
        iterator.next();
    });
    iterator.close();
});

if (require.main === module.id) {
    run(exports);
}