// stdlib
var assert = require("assert");
importPackage(org.ringojs.repository);
// custom
var {moduleDoc, moduleList} = require('../jsdocserializer');

var fooBarRepo = new ZipRepository(module.resolve('foobarRepository.zip'));

var moduleListExpected = [
    {
        "id": "lib/barzar/barzo",
        "fileoverview": "Deeper Module gets detected"
    },
    {
        "id": "lib/zar",
        "fileoverview": "fileoverview Zar"
    }
];

var moduleDocExpected = {
    "name": "lib/zar",
    "fileoverview": "fileoverview Zar",
    "example": "This example demonstrates\n how Zar can be used.",
    "since": null,
    "deprecated": null,
    "items": [
        {
            "name": "Zar",
            "shortName": "Zar",
            "relatedClass": null,
            "desc": "Zar class constructor for constructing Zar classes.",
            "isClass": true,
            "isFunction": true,
            "isStatic": true,
            "parameters": [
                {
                    "name": "stringParam",
                    "type": "String",
                    "desc": "a string parameter"
                },
                {
                    "name": "numberParam",
                    "type": "Number",
                    "desc": "a number parameter"
                }
            ],
            "throws": [
                "Error might throw error if revolution fails"
            ],
            "sees": [
                "<a href=\"http://en.wikipedia.org/wiki/Tsar\">http://en.wikipedia.org/wiki/Tsar</a>"
            ],
            "returns": {
                "name": " a Zar instance",
                "type": "Zar"
            },
            "example": null,
            "since": null,
            "deprecated": null
        },
        {
            "name": "Zar.defineMultiOne",
            "shortName": "defineMultiOne",
            "relatedClass": "Zar",
            "desc": "First property in defineProperties",
            "isClass": false,
            "isFunction": undefined,
            "isStatic": true,
            "parameters": [

            ],
            "throws": [

            ],
            "sees": [

            ],
            "returns": {
                "name": null,
                "type": "Boolean"
            },
            "example": null,
            "since": null,
            "deprecated": null
        },
        {
            "name": "Zar.defineMultiTwo",
            "shortName": "defineMultiTwo",
            "relatedClass": "Zar",
            "desc": "Second property in defineProperties",
            "isClass": false,
            "isFunction": undefined,
            "isStatic": true,
            "parameters": [

            ],
            "throws": [

            ],
            "sees": [

            ],
            "returns": {
                "name": null,
                "type": "Number"
            },
            "example": null,
            "since": null,
            "deprecated": null
        },
        {
            "name": "Zar.prototype.deprecateMe",
            "shortName": "deprecateMe",
            "relatedClass": "Zar",
            "desc": "This property shall be deprecated",
            "isClass": false,
            "isFunction": undefined,
            "isStatic": false,
            "parameters": [

            ],
            "throws": [

            ],
            "sees": [

            ],
            "returns": {
                "name": null,
                "type": null
            },
            "example": null,
            "since": null,
            "deprecated": "don't use this"
        },
        {
            "name": "Zar.prototype.instanceFn",
            "shortName": "instanceFn",
            "relatedClass": "Zar",
            "desc": "Instance Function",
            "isClass": false,
            "isFunction": true,
            "isStatic": false,
            "parameters": [
                {
                    "name": "doSomething",
                    "type": "Boolean",
                    "desc": "param is not visible in function def"
                }
            ],
            "throws": [

            ],
            "sees": [

            ],
            "returns": {
                "name": null,
                "type": null
            },
            "example": null,
            "since": null,
            "deprecated": null
        },
        {
            "name": "Zar.prototype.zarPrototype",
            "shortName": "zarPrototype",
            "relatedClass": "Zar",
            "desc": "Instance property",
            "isClass": false,
            "isFunction": undefined,
            "isStatic": false,
            "parameters": [

            ],
            "throws": [

            ],
            "sees": [

            ],
            "returns": {
                "name": null,
                "type": null
            },
            "example": null,
            "since": null,
            "deprecated": null
        },
        {
            "name": "Zar.prototype.zarPrototypeProp",
            "shortName": "zarPrototypeProp",
            "relatedClass": "Zar",
            "desc": "A Prototype property.",
            "isClass": false,
            "isFunction": undefined,
            "isStatic": false,
            "parameters": [

            ],
            "throws": [

            ],
            "sees": [

            ],
            "returns": {
                "name": null,
                "type": null
            },
            "example": null,
            "since": null,
            "deprecated": null
        },
        {
            "name": "Zar.prototype.zarPrototypeTwo",
            "shortName": "zarPrototypeTwo",
            "relatedClass": "Zar",
            "desc": "A prototype function",
            "isClass": false,
            "isFunction": true,
            "isStatic": false,
            "parameters": [

            ],
            "throws": [

            ],
            "sees": [

            ],
            "returns": {
                "name": null,
                "type": null
            },
            "example": null,
            "since": null,
            "deprecated": null
        },
        {
            "name": "Zar.zarDefine",
            "shortName": "zarDefine",
            "relatedClass": "Zar",
            "desc": "Single defineProperty",
            "isClass": false,
            "isFunction": undefined,
            "isStatic": true,
            "parameters": [

            ],
            "throws": [

            ],
            "sees": [

            ],
            "returns": {
                "name": null,
                "type": null
            },
            "example": null,
            "since": null,
            "deprecated": null
        },
        {
            "name": "Zar.zarStatic",
            "shortName": "zarStatic",
            "relatedClass": "Zar",
            "desc": "A static property",
            "isClass": false,
            "isFunction": undefined,
            "isStatic": true,
            "parameters": [

            ],
            "throws": [

            ],
            "sees": [

            ],
            "returns": {
                "name": null,
                "type": null
            },
            "example": null,
            "since": null,
            "deprecated": null
        },
        {
            "name": "Zar.zarStaticFn",
            "shortName": "zarStaticFn",
            "relatedClass": "Zar",
            "desc": "A static function",
            "isClass": undefined,
            "isFunction": true,
            "isStatic": true,
            "parameters": [

            ],
            "throws": [

            ],
            "sees": [

            ],
            "returns": {
                "name": " a true or false value",
                "type": "Boolean"
            },
            "example": null,
            "since": null,
            "deprecated": null
        }
    ]
};


exports.testModuleDoc = function() {
    assert.deepEqual(moduleDocExpected, moduleDoc(fooBarRepo, 'lib/zar'));
};

exports.testModuleList = function() {
    assert.deepEqual(moduleListExpected, moduleList(fooBarRepo, true));
};

if (require.main == module.id) {
    require('test').run(exports);
}
