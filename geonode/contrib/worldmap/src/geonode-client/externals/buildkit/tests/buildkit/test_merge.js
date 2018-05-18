var ASSERT = require("assert");
var MERGE = require("buildkit/merge");
var clone = require("ringo/utils/objects").clone;

var assets = {
    
    "pet/dog/chiwawa.js" : {include: {"trick/tailwag.js": true}, require: {"pet/dog.js": true}},
    
    "trick/tailwag.js": {include: {}, require: {"trick.js": true}},
    
    "pet/dog.js": {include: {"trick/tailwag.js": true}, require: {"pet.js": true}},

    "pet.js": {include: {}, require: {}},
    
    "trick.js": {include: {}, require: {}},

    "pet/cat/manx.js": {include: {}, require: {"pet/cat.js": true}},
    
    "pet/cat.js": {include: {}, require: {"pet.js": true}}
    
};

// since the merge modifies assets, we create a fresh clone each time
function getAssets() {
    return clone(assets, {}, true);
}

exports["test: _getOrderedAssets (all)"] = function() {


    var first = [];
    var include = [];
    var exclude = [];
    var last = [];
    var ordered = MERGE._getOrderedAssets(first, include, exclude, last, getAssets());
    
    var count = 0;
    for (var path in getAssets()) {
        ++count;
        ASSERT.isTrue(ordered.indexOf(path) >= 0, path + " in ordered");
    }
    ASSERT.strictEqual(ordered.length, count, "correct ordered length");
    
    ASSERT.isTrue(ordered.indexOf("pet.js") < ordered.indexOf("pet/dog.js"), "pet before pet/dog.js");
    ASSERT.isTrue(ordered.indexOf("pet/dog.js") < ordered.indexOf("pet/dog/chiwawa.js"), "pet/dog.js before pet/dog/chiwawa.js");
    
    ASSERT.isTrue(ordered.indexOf("pet.js") < ordered.indexOf("pet/cat.js"), "pet.js before pet/cat.js");
    ASSERT.isTrue(ordered.indexOf("pet/cat.js") < ordered.indexOf("pet/cat/manx.js"), "pet/cat before pet/cat/manx.js");
    
    ASSERT.isTrue(ordered.indexOf("trick.js") < ordered.indexOf("trick/tailwag.js"), "trick.js before trick/tailwag.js");

};

exports["test: _getOrderedAssets (first I)"] = function() {

    var first = ["trick.js"];
    var include = ["pet/dog/chiwawa.js"];
    var exclude = [];
    var last = [];
    var ordered = MERGE._getOrderedAssets(first, include, exclude, last, getAssets());
    
    ASSERT.strictEqual(ordered.indexOf("pet/cat.js"), -1, "no pat/cat.js here");
    
    ASSERT.isTrue(ordered.indexOf("pet.js") < ordered.indexOf("pet/dog.js"), "pet.js before pet/dog.js");
    ASSERT.isTrue(ordered.indexOf("pet/dog.js") < ordered.indexOf("pet/dog/chiwawa.js"), "pet/dog.js before pet/dog/chiwawa.js");
    
    ASSERT.isTrue(ordered.indexOf("trick/tailwag.js") >= 0, "trick/tailwag.js included by default");
    ASSERT.strictEqual(ordered.indexOf("trick.js"), 0, "trick first");
    
}

exports["test: _getOrderedAssets (first II)"] = function() {

    var first = ["pet.js"];
    var include = ["pet/dog/chiwawa.js"];
    var exclude = [];
    var last = [];
    var ordered = MERGE._getOrderedAssets(first, include, exclude, last, getAssets());
    
    ASSERT.strictEqual(ordered.indexOf("pet/cat.js"), -1, "no pat/cat.js here");
    
    ASSERT.isTrue(ordered.indexOf("pet.js") < ordered.indexOf("pet/dog.js"), "pet.js before pet/dog.js");
    ASSERT.isTrue(ordered.indexOf("pet/dog.js") < ordered.indexOf("pet/dog/chiwawa.js"), "pet/dog.js before pet/dog/chiwawa.js");
    
    ASSERT.isTrue(ordered.indexOf("trick/tailwag.js") >= 0, "trick/tailwag.js included by default");
    ASSERT.isTrue(ordered.indexOf("trick.js") < ordered.indexOf("trick/tailwag.js"), "trick.js before trick/tailwag");

    ASSERT.strictEqual(ordered.indexOf("pet.js"), 0, "pet.js first");

};

exports["test: _getOrderedAssets (include)"] = function() {

    var first = [];
    var include = ["pet/dog/chiwawa.js"];
    var exclude = [];
    var last = [];
    var ordered = MERGE._getOrderedAssets(first, include, exclude, last, getAssets());
    
    ASSERT.strictEqual(ordered.indexOf("pet/cat.js"), -1, "no pat/cat.js here");
    
    ASSERT.isTrue(ordered.indexOf("pet.js") < ordered.indexOf("pet/dog.js"), "pet.js before pet/dog.js");
    ASSERT.isTrue(ordered.indexOf("pet/dog.js") < ordered.indexOf("pet/dog/chiwawa.js"), "pet/dog.js before pet/dog/chiwawa.js");
    
    ASSERT.isTrue(ordered.indexOf("trick/tailwag.js") >= 0, "trick/tailwag.js included by default");
    ASSERT.isTrue(ordered.indexOf("trick.js") < ordered.indexOf("trick/tailwag.js"), "trick.js before trick/tailwag.js");

};

exports["test: _getOrderedAssets (exclude overrules include directive)"] = function() {

    var first = [];
    var include = ["pet/dog/chiwawa.js"];
    var exclude = ["trick/"];
    var last = [];
    var ordered = MERGE._getOrderedAssets(first, include, exclude, last, getAssets());
    
    ASSERT.strictEqual(ordered.indexOf("pet/cat.js"), -1, "no pat/cat.js here");
    
    ASSERT.isTrue(ordered.indexOf("pet.js") < ordered.indexOf("pet/dog.js"), "pet before pet/dog.js");
    ASSERT.isTrue(ordered.indexOf("pet/dog.js") < ordered.indexOf("pet/dog/chiwawa.js"), "pet/dog.js before pet/dog/chiwawa.js");
    
    ASSERT.strictEqual(ordered.indexOf("trick/tailwag.js"), -1, "trick/tailwag.js excluded");
    ASSERT.strictEqual(ordered.indexOf("trick.js"), -1, "no trick.js");

};

exports["test: _getOrderedAssets (exclude overrules require directive)"] = function() {

    var first = [];
    var include = ["pet/dog.js"]; // dog has a direct dependency on pet
    var exclude = ["pet.js"]; // but we're going to explicitly exclude this dependency
    var last = [];
    var ordered = MERGE._getOrderedAssets(first, include, exclude, last, getAssets());
    
    ASSERT.isTrue(ordered.indexOf("pet/dog.js") > -1, "got pet/dog.js");    
    ASSERT.strictEqual(ordered.indexOf("pet.js"), -1, "no pet.js");

};

exports["test: _getOrderedAssets (exclude overrules require directive - transitive)"] = function() {

    var first = [];
    var include = ["pet/dog/chiwawa.js"]; // chiwawa has a transitive dependency on pet
    var exclude = ["pet.js"]; // but we're going to explicitly exclude this dependency
    var last = [];
    var ordered = MERGE._getOrderedAssets(first, include, exclude, last, getAssets());
    
    ASSERT.isTrue(ordered.indexOf("pet/dog.js") < ordered.indexOf("pet/dog/chiwawa.js"), "pet/dog.js before pet/dog/chiwawa.js");    
    ASSERT.strictEqual(ordered.indexOf("pet.js"), -1, "no pet.js");

};


exports["test: _getOrderedAssets (last)"] = function() {

    var first = [];
    var include = [];
    var exclude = [];
    var last = ["pet/cat/manx.js"];
    var ordered = MERGE._getOrderedAssets(first, include, exclude, last, getAssets());
    
    var count = 0;
    for (var path in getAssets()) {
        ++count;
        ASSERT.isTrue(ordered.indexOf(path) >= 0, path + " in ordered");
    }
    ASSERT.strictEqual(ordered.length, count, "correct ordered length");
    
    ASSERT.isTrue(ordered.indexOf("pet.js") < ordered.indexOf("pet/dog.js"), "pet.js before pet/dog.js");
    ASSERT.isTrue(ordered.indexOf("pet/dog.js") < ordered.indexOf("pet/dog/chiwawa.js"), "pet/dog.js before pet/dog/chiwawa.js");
    
    ASSERT.isTrue(ordered.indexOf("pet.js") < ordered.indexOf("pet/cat.js"), "pet.js.js before pet/cat");
    ASSERT.isTrue(ordered.indexOf("pet/cat.js") < ordered.indexOf("pet/cat/manx.js"), "pet/cat before pet/cat/manx.js");
    
    ASSERT.isTrue(ordered.indexOf("trick.js") < ordered.indexOf("trick/tailwag.js"), "trick.js before trick/tailwag.js");
    
    ASSERT.strictEqual(ordered.indexOf("pet/cat/manx.js"), count-1, "pet/cat/manx.js last");

};

exports["test: _getOrderedAssets (circular)"] = function() {
    
    var circular = {
        "happiness.js": {require: {"money.js": true}},
        "money.js": {require: {"happiness.js": true}}
    };
    
    var first = [];
    var include = [];
    var exclude = [];
    var last = [];
    var ordered = MERGE._getOrderedAssets(first, include, exclude, last, circular);
    
    ASSERT.strictEqual(ordered.length, 2, "correct ordered length");

    var first = ["happiness.js"];
    var include = [];
    var exclude = [];
    var last = [];
    var ordered = MERGE._getOrderedAssets(first, include, exclude, last, circular);

    ASSERT.strictEqual(ordered.indexOf("happiness.js"), 0, "happiness.js first");


    var first = ["money.js"];
    var include = [];
    var exclude = [];
    var last = [];
    var ordered = MERGE._getOrderedAssets(first, include, exclude, last, circular);

    ASSERT.strictEqual(ordered.indexOf("money.js"), 0, "money first.js");

};


if (require.main == module.id) {
    system.exit(require("test").run(exports));
}
