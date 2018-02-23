var ASSETS = require("./assets");
var TSORT = require("./tsort");
var FS = require("fs");

var _getOrderedAssets = function(first, include, exclude, last, assets) {

    // no include means include all
    if (include.length === 0) {
        for (var path in assets) {
            include.push(path);
        }
    }

    // determine which files to omit based on exclude list
    var omit = {};
    exclude.forEach(function(path) {
        omit[path] = true;
    });

    var unordered = {};
    first.concat(include, last).forEach(function(path) {
        if (!shouldOmit(omit, path)) {
            unordered[path] = true;
        }
    });
    
    // pull in all includes and requires declared in code
    unordered = expand(unordered, omit, assets);
    for (var path in unordered) {
        unordered[path] = assets[path].require;
    };
    
    // topo sort of assets based on requires
    var ordered = TSORT.sort(unordered);
    
    // pull out any assets declared in first or last
    ordered = ordered.filter(function(asset) {
        return (first.indexOf(asset) < 0 && last.indexOf(asset) < 0);
    });
    
    // order based on first, includes (sorted by requires), last
    return first.concat(ordered, last);

};

function shouldOmit(omit, path) {
    var should = (path in omit);
    if (!should) {
        for (var pattern in omit) {
            if (path.indexOf(pattern) === 0) {
                should = true;
                break
            }
        }
    }
    return should;
}

var expand = function(unordered, omit, assets) {
    var path, entry, require, include, newlyIncluded, expanded = true;
    while (expanded) {
        expanded = false;
        newlyIncluded = {};
        for (path in unordered) {
            newlyIncluded[path] = true;
            // expand to include requires & includes from assets
            entry = assets[path];
            if (entry) {
                for (require in entry.require) {
                    if (shouldOmit(omit, require)) {
                        // delete require if it was listed in exclude
                        delete entry.require[require];
                    } else if (!(unordered[require])) {
                        expanded = true;
                        newlyIncluded[require] = true;
                    }
                }
                for (include in entry.include) {
                    if (!shouldOmit(omit, include) && !unordered[include]) {
                        expanded = true;
                        newlyIncluded[include] = true;
                    }
                }
            } else {
                throw "Entry not found in assets: " + path;
            }
        }
        unordered = newlyIncluded;
    }
    return unordered;
};

var order = function(config) {
    var assets = ASSETS.compile(config.root);
    var first = config.first || [];
    var include = config.include || [];
    var exclude = config.exclude || [];
    var last = config.last || [];
    var ordered = _getOrderedAssets(first, include, exclude, last, assets);
    var scripts = ordered.map(function(path) {
        return {
            path: path,
            root: assets[path].root
        };
    });
    return scripts;
};

var concat = function(config) {
    var sources = order(config).map(function(script) {
        var file, source = "/** FILE: " + script.path + " **/\n";
        file = FS.join(script.root, script.path);
        if (FS.exists(file)) {
            source += FS.read(file);
        } else {
            throw new Error("Can't find script: " + file);
        }
        return source;
    });
    return sources.join("\n");
};

exports._getOrderedAssets = _getOrderedAssets;
exports.order = order;
exports.concat = concat;
