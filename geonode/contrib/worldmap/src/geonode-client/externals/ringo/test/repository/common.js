var assert = require("assert");
var {absolute, join} = require("fs");
var strings = require("ringo/utils/strings");
var {separator} = java.io.File;

exports.setup = function(exports, path, repo) {

    exports.testGetResource = function() {
        var res = repo.getResource("test.txt");
        assert.strictEqual(res.name, "test.txt");
        assert.isTrue(res.exists());
        assert.strictEqual(res.baseName, "test");
        // Regardless of OS, when resolving paths inside an archive file the separator is '/'.
        var comparePath = /\.zip$|\.jar$/.test(path) ? absolute(path) + "/test.txt" : absolute(join(path, "test.txt"));
        assert.strictEqual(res.path, comparePath);
        assert.strictEqual(res.content, "hello world!");
    };

    exports.testGetNestedResource = function() {
        var res = repo.getResource("nested/nested.txt");
        assert.strictEqual(res.name, "nested.txt");
        assert.isTrue(res.exists());
        assert.strictEqual(res.baseName, "nested");
        // Regardless of OS, when resolving paths inside an archive file the separator is '/'.
        var comparePath = /\.zip$|\.jar$/.test(path)
                ? absolute(path) + "/nested/nested.txt"
                : absolute(join(path, "nested", "nested.txt"));
        assert.strictEqual(res.path, comparePath);
        // Windows uses two bytes for EOL while other OS's use one byte.
        var len = /^windows/.test(java.lang.System.getProperty("os.name", "generic").toLowerCase()) ? 2274 : 2240;
        // Except when in an archive, then it depends on what OS the archive was created, ugh.
        if (/\.zip$|\.jar$/.test(path)) len = 2240;
        assert.strictEqual(res.length, len);
        assert.strictEqual(res.content.length, len);
        assert.isTrue(strings.startsWith(res.content, "Lorem ipsum dolor sit amet"));
        assert.isTrue(strings.endsWith(res.content.trim(), "id est laborum."));
    };

    exports.testNonExistingResource = function() {
        var res = repo.getResource("doesNotExist.txt");
        assert.isNotNull(res);
        assert.isFalse(res.exists());
        assert.throws(function() {res.content});
    };

    exports.testNestedNonExistingResource = function() {
        var res = repo.getResource("foo/bar/doesNotExist.txt");
        assert.isNotNull(res);
        assert.isFalse(res.exists());
        assert.throws(function() {res.content});
    };

    exports.testGetRepositories = function() {
        var repos = repo.getRepositories();
        assert.strictEqual(repos.length, 1);
        assert.strictEqual(repos[0].name, "nested");
    }

    exports.testGetResources = function() {
        var res = repo.getResources();
        assert.strictEqual(res.length, 1);
        assert.strictEqual(res[0].name, "test.txt");
    }

    exports.testGetRecursiveResources = function() {
        var res = repo.getResources(true);
        assert.strictEqual(res.length, 2);
        res = res.sort(function(a, b) a.length - b.length);
        assert.strictEqual(res[0].name, "test.txt");
        assert.strictEqual(res[0].relativePath, "test.txt");
        // Regardless of OS, when resolving paths inside an archive file the separator is '/'.
        var comparePath = /\.zip$|\.jar$/.test(path) ? absolute(path) + "/test.txt" : absolute(join(path, "test.txt"));
        assert.strictEqual(res[0].path, comparePath);
        assert.strictEqual(res[1].name, "nested.txt");
        assert.strictEqual(res[1].relativePath, "nested/nested.txt");
        // Regardless of OS, when resolving paths inside an archive file the separator is '/'.
        var comparePath = /\.zip$|\.jar$/.test(path) ? absolute(path) + "/nested/nested.txt" : absolute(join(path, "nested/nested.txt"));
        assert.strictEqual(res[1].path, comparePath);
    }

    exports.testGetNestedResources = function() {
        var res = repo.getResources("nested", false);
        assert.strictEqual(res.length, 1);
        assert.strictEqual(res[0].name, "nested.txt");
        assert.strictEqual(res[0].relativePath, "nested/nested.txt");
    }

};
