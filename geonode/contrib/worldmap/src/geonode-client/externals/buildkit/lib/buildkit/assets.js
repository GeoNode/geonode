var FS = require("fs");

var JS_RE = /\.js$/;
var REQUIRE_RE = /^\s\**\s*@requires?\s+([\w\/]+\.js)\s*$/;
var INCLUDE_RE = /^\s\**\s*@includes?\s+([\w\/]+\.js)\s*$/;

var compile = function(roots) {
    var assets = {};
    roots.forEach(function(root) {
        FS.listTree(root).forEach(function(path) {
            if (FS.isFile(FS.join(root, path)) && JS_RE.test(path)) {
                assets[path.replace(/\\/g, "/")] = getDependencies(root, path);
            }
        });
    });
    return assets;    
};

var getDependencies = function(root, path) {
    var file = FS.join(root, path);
    var source = FS.read(file);
    var require = {};
    var include = {};
    source.split("\n").forEach(function(line) {
        var match = line.match(REQUIRE_RE);
        if (match) {
            require[match[1]] = true;
        }
        match = line.match(INCLUDE_RE);
        if (match) {
            include[match[1]] = true;
        }
    });
    return {
        root: root,
        include: include,
        require: require
    };
};

exports.compile = compile;
