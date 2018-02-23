var ASSERT = require("assert");
var ASSETS = require("buildkit/assets");
var OBJECTS = require("ringo/utils/objects");
var FS = require("fs");

var base = module.resolve("../integration");

exports["test: compile (animal)"] = function() {
    var roots = [FS.join(base, "animal", "lib")];
    var assets = ASSETS.compile(roots);
    var expect = {
        "animal.js": {
            "root": roots[0],
            "include": {},
            "require": {}
        },
        "animal/mammal.js": {
            "root": roots[0],
            "include": {},
            "require": {
                "animal.js": true
            }
        },
        "animal/mammal/monkey.js": {
            "root": roots[0],
            "include": {},
            "require": {
                "animal/mammal.js": true,
                "food/fruit/banana.js": true
            }
        },
        "animal/reptile.js": {
            "root": roots[0],
            "include": {},
            "require": {
                "animal.js": true
            }
        },
        "animal/reptile/lizard.js": {
            "root": roots[0],
            "include": {},
            "require": {
                "animal/reptile.js": true,
                "food/vegetable/carrot.js": true
            }
        }
    };
    ASSERT.deepEqual(assets, expect, "animal assets");
};

exports["test: compile (food)"] = function() {
    var roots = [FS.join(base, "food", "lib")];
    var assets = ASSETS.compile(roots);
    var expect = {
        "food.js": {
            "root": roots[0],
            "include": {},
            "require": {}
        },
        "food/fruit.js": {
            "root": roots[0],
            "include": {},
            "require": {
                "food.js": true
            }
        },
        "food/fruit/banana.js": {
            "root": roots[0],
            "include": {},
            "require": {
                "food/fruit.js": true
            }
        },
        "food/vegetable.js": {
            "root": roots[0],
            "include": {},
            "require": {
                "food.js": true
            }
        },
        "food/vegetable/carrot.js": {
            "root": roots[0],
            "include": {},
            "require": {
                "food/vegetable.js": true
            }
        }
    };
    ASSERT.deepEqual(assets, expect, "food assets");
};

exports["test: compile (places)"] = function() {
    var roots = [FS.join(base, "places", "lib")];
    var assets = ASSETS.compile(roots);
    var expect = {
       "places.js": {
           "root": roots[0],
           "include": {},
           "require": {}
       },
       "places/zoo.js": {
           "root": roots[0],
           "include": {},
           "require": {
               "places.js": true,
               "animal/mammal/monkey.js": true,
               "animal/reptile/lizard.js": true
           }
       }
    };
    ASSERT.deepEqual(assets, expect, "places assets");
};

exports["test: compile (all)"] = function() {
    var roots = [
        FS.join(base, "animal", "lib"),
        FS.join(base, "food", "lib"),
        FS.join(base, "places", "lib"),
    ];
    var assets = ASSETS.compile(roots);
    var animal = ASSETS.compile([roots[0]]);
    var food = ASSETS.compile([roots[1]]);
    var places = ASSETS.compile([roots[2]]);
    var expect = OBJECTS.merge(animal, food, places);
    ASSERT.deepEqual(assets, expect, "all assets");
}

if (require.main == module.id) {
    system.exit(require("test").run(exports));
}
