/**
 * @fileOverview Low level support for parsing JSDoc-style comments from JavaScript files.
 */

var strings = require('ringo/utils/strings');
var arrays = require('ringo/utils/arrays');
var {Parser, Token, getTypeName} = require('ringo/parser');
var {Buffer} = require('ringo/buffer');

importPackage(org.mozilla.javascript);
importPackage(org.ringojs.repository);

var log = require('ringo/logging').getLogger(module.id);

var standardObjects = [
    'Array', 'Object', 'String', 'Date', 'Number', 'RegExp', 'Boolean'
];

/**
 * Create a script repository for the given path
 * @param {String} path the base path
 * @returns an script repository
 */
exports.ScriptRepository = function(path) {
    return new ScriptRepository(path);
};

function ScriptRepository(path) {
    var repo = path instanceof Repository ?
               path : new FileRepository(path);

    /**
     * Get a list of script resources (files with a .js extension) in this
     * repository.
     * @param {Boolean} nested whether to return scripts in nested directories
     * @returns {Array} list of script files as RingoJS Resource objects
     */
    this.getScriptResources = function(nested) {
        var list = repo.getResources(Boolean(nested));
        return list.filter(function(r) {return strings.endsWith(r.name, '.js');});
    };

    /**
     * Get a script resource contained in this repository.
     * @param {String} path the script path
     * @returns {Resource} the script resource
     */
    this.getScriptResource = function(path) {
        return repo.getResource(path);
    };

    /**
     * Check whether this script repository exists.
     * @returns {boolean} true if the repository exists
     */
    this.exists = function() {
        return repo.exists();
    };

    /**
     * Get the absolute path of this script repository.
     * @returns {string} the absolute repository path
     */
    this.getPath = function() {
        return repo.getPath();
    };

}

/**
 * Parse a script resource and return an array containing the JSDoc items
 * for the properties it exports.
 * @param {Resource} resource a script resource
 * @returns {Array} an array of objects representing the API documentation for
 *     of the resource
 */
exports.parseResource = function(resource) {
    var exportedFunction;
    var exportedName;
    var exported = [];
    var jsdocs = [];
    var dict = {};

    var checkAssignment = function(node, root, exported) {
        if (node.type == Token.ASSIGN) {
            if (node.left.type == Token.GETPROP) {
                var target = node.left.target;
                var name = node.left.property.string;
                var propname = nodeToString(node.left);
                if (strings.startsWith(propname, 'exports.') && !arrays.contains(exported, name)) {

                    addDocItem(name, root.jsDoc, node.right);
                    exported.push(name);
                    if (node.right.type == Token.FUNCTION) {
                        exportedFunction = node.right;
                        exportedName = name;
                    }
                } else if (target.type == Token.THIS) {
                    if (isGreatGrandMa(exportedFunction, root)) {
                        addDocItem(exportedName + ".prototype." + name, root.jsDoc, node.right);
                        /* if (node.right.type == Token.FUNCTION) {
                         exportedFunction = node.right;
                         exportedName = exportedName + ".prototype." + name;
                         } */
                    } else if (arrays.contains(exported, name)
                                    && getNestingLevel(node) === 2) {
                        addDocItem(name, root.jsDoc, node.right);
                    }
                } else {
                    var chain = propname.split(".");
                    if (arrays.contains(exported, chain[0])) {
                        // Foo.bar or Foo.prototype.bar assignment where Foo is exported
                        addDocItem(propname, root.jsDoc, node.right);
                    }
                }
            } else if (node.left.type == Token.GETELEM
                    && node.left.target.type == Token.NAME
                    && node.left.target.string == "exports"
                    && node.left.element.type == Token.STRING) {
                // exports["foo"] = bar
                addDocItem(node.left.element.value, root.jsDoc, node.right);
            }
        }
    };

    var addDocItem = function(name, jsdoc, value) {
        jsdoc = extractTags(jsdoc);
        if (jsdoc.getTag("ignore") != null) {
            return;
        }
        if (!name) {
            name = jsdoc.getTag("name");
            var memberOf = jsdoc.getTag("memberOf");
            if (memberOf) {
                name = memberOf + "." + name;
            }
        }
        // If an empty doc item for the name already exists replace it
        // with the new one.
        var previous = dict[name];
        if (previous) {
            if (jsdoc.tags.length && !previous.tags.length) {
                previous.tags = jsdoc.tags;
            }
            jsdoc = previous;
        } else {
            jsdoc.name = name;
            jsdocs.push(jsdoc);
            dict[name] = jsdoc;
        }
        if ((value && value.type == Token.FUNCTION)
                || jsdoc.getTag("function") != null
                || jsdoc.getTag("param") != null
                || jsdoc.getTag("returns") != null
                || jsdoc.getTag("constructor") != null) {
            jsdoc.isFunction = true;
            // extract params
            if (value && value.type == Token.FUNCTION) {
                jsdoc.params = value.getParams().toArray().map(function(p) nodeToString(p));
            }
        }
        if (jsdoc.getTag("constructor") != null
                || jsdoc.getTag("class") != null) {
            jsdoc.isClass = true;
        }
    };

    new Parser({parseComments: true}).visit(resource, function(node) {
        // loop through all comments looking for dangling jsdocs
        if (node.type == Token.SCRIPT && node.comments) {
            for each (var comment in node.comments.toArray()) {
                if (comment.commentType == Token.CommentType.JSDOC) {
                    if (/@fileoverview\s/i.test(comment.value)) {
                        Object.defineProperty(jsdocs, "fileoverview", {
                            value: extractTags(comment.value)
                        });
                    } else if (/@name\s/i.test(comment.value)) {
                        // JSDoc comments that have an explicit @name tag are used as is
                        // without further AST introspection. This can be used to document
                        // APIS that have no corresponding code, e.g. native host methods
                        addDocItem(null, comment.value);
                    }
                }
            }
        }
        // export("foo")
        if (node.type == Token.CALL && node.target.type == Token.NAME && node.target.string == "export") {
            for each (var arg in ScriptableList(node.arguments)) {
                if (arg.type == Token.STRING) exported.push(arg.value);
            }
        }
        // check for Object.defineProperty(foo, bar, {})
        if (node.type == Token.CALL && node.target.type == Token.GETPROP) {
            var getprop = node.target;
            if (getprop.target.type == Token.NAME && getprop.target.string == "Object"
                    && getprop.property.string == "defineProperty") {
                var args = ScriptableList(node.arguments);
                var target = nodeToString(args[0]).split('.');
                var jsdoc, value;
                // rhino puts jsdoc on the first name of the third argument object literal (property descriptor)
                if (args[2] && args[2].elements) {
                    var left = args[2].elements.get(0).left;
                    jsdoc = left.jsDoc;
                    if (nodeToString(left) == "value") {
                        value = args[2].elements.get(0).right;
                    }
                }
                if (arrays.contains(exported, target[0]) || arrays.contains(standardObjects, target[0])) {
                    target.push(nodeToString(args[1]));
                    addDocItem(target.join('.'), jsdoc, value);
                } else if (target[0] == 'this' && isGreatGrandMa(exportedFunction, node)) {
                    target[0] = exportedName;
                    target.push('prototype', nodeToString(args[1]));
                    addDocItem(target.join('.'), jsdoc, value);
                }
            }
        }

        // check for Object.defineProperties(foo, {bar: {}})
        if (node.type == Token.CALL && node.target.type == Token.GETPROP) {
            var getprop = node.target;
            if (getprop.target.type == Token.NAME && getprop.target.string == "Object"
                    && getprop.property.string == "defineProperties") {
                var args = ScriptableList(node.arguments);
                var target = nodeToString(args[0]).split('.');
                var jsdoc, value;

                var isExported = false;
                if (arrays.contains(exported, target[0]) || arrays.contains(standardObjects, target[0])) {
                    isExported = true;
                } else if (target[0] == 'this' && exportedFunction != null) {
                    target[0] = exportedName;
                    target.push('prototype');
                    isExported = true;
                }
                if (isExported && args[1] && args[1].elements) {
                    // check for object literal holding multiple property descs
                    var elements = args[1].elements;
                    for (var i = 0, l = elements.size(); i < l; i++) {
                        var left = elements.get(i).left;
                        value = nodeToString(left);
                        target.push(value);
                        jsdoc = left.jsDoc;
                        addDocItem(target.join('.'), jsdoc, value);
                        target.pop();
                    }
                }
            }
        }

        // check for __define[GS]etter__
        if (node.type == Token.CALL && node.target.type == Token.GETPROP) {
            var getprop = node.target;
            if (arrays.contains(["__defineGetter__", "__defineSetter__"], getprop.property.string)) {
               var args = ScriptableList(node.arguments);
               var target = nodeToString(node.target).split('.');
               var jsdoc = args[1].jsDoc;
               var name = nodeToString(args[0]);
               // prototype.__defineGetter__
               if (arrays.contains(exported, target[0]) || arrays.contains(standardObjects, target[0])) {
                  target.pop();
                  target.push(name);
                  addDocItem(target.join('.'), jsdoc);
               // this.__defineGetter__
               } else if (target[0] == 'this' && exportedFunction != null) {
                  addDocItem(exportedName + ".prototype." + name, jsdoc, exported);
               }
            }
        }
        // exported function
        if (node.type == Token.FUNCTION && (arrays.contains(exported, node.name) || /@name\s/.test(node.jsDoc))) {
            addDocItem(node.name, node.jsDoc, node);
            exportedFunction = node;
            exportedName = node.name;
        }
        // var foo = exports.foo = bar
        if (node.type == Token.VAR || node.type == Token.LET) {
            for each (var n in ScriptableList(node.variables)) {
                if (n.target.type == Token.NAME && arrays.contains(exported, n.target.string)) {
                    if (getNestingLevel(node) == 1) {
                        if (n.initializer && n.initializer.type == Token.FUNCTION) {
                            // Note: We might still miss something like
                            // var foo = XXX.foo = function()...
                            exportedFunction = n.initializer;
                            exportedName = n.target.string;
                        }
                        addDocItem(n.target.string,  node.jsDoc, n.initializer);
                    }
                } else if (n.initializer && n.initializer.type == Token.ASSIGN) {
                    checkAssignment(n.initializer, node, exported);
                }
            }
        }
        // exports.foo = bar
        if (node.type == Token.ASSIGN) {
            checkAssignment(node, node, exported);
        }

        return true;
    });

    return jsdocs.sort(function(a, b) {
        return a.name < b.name ? -1 : 1;
    });
};

/**
 * Remove slash-star comment wrapper from a raw comment string.
 * @type String
 */
function unwrapComment(/**String*/comment) {
    return comment ? comment.replace(/(^\/\*\*|\*\/$)/g, "").replace(/^\s*\* ?/gm, "") : "";
}

/**
 * Parse a JSDoc comment into an object wrapping an array of tags as [tagname, tagtext]
 * and getTag() and getTags() methods to lookup specific tags.
 * @param {String} comment the raw JSDoc comment
 * @returns {Object} an array of tags.
 */
function extractTags(/**String*/comment) {
    if (!comment) {
        comment = "";
    } else if (strings.startsWith(comment, "/**")) {
        comment = unwrapComment(comment).trim();
    }
    var tags = comment.split(/(^|[\r\n])\s*@/)
            .filter(function($){ return $.match(/\S/); });
    tags = tags.map(function(tag, idx) {
        if (idx == 0 && !strings.startsWith(comment, '@')) {
            return ['desc', tag.trim()];
        } else {
            var space = tag.search(/\s/);
            return space > -1 ?
                   [tag.substring(0, space).toLowerCase(),
                       tag.substring(space + 1).trim()] :
                   [tag.toLowerCase(), ''];
        }
    });
    return Object.create(docProto, {
        tags: {value: tags, writable: true, enumerable: true}
    });
}

// the prototype used for document items
var docProto = {
    getTag: function(name) {
        name = name.toLowerCase();
        for (var i = 0; i < this.tags.length; i++) {
            if (this.tags[i][0] == name) return this.tags[i][1];
        }
        return null;
    },
    getTags: function(name) {
        name = name.toLowerCase();
        var result = [];
        for (var i = 0; i < this.tags.length; i++) {
            if (this.tags[i][0] == name) result.push(this.tags[i][1]);
        }
        return result;
    },
    getParameterList: function() {
        if (!this.parameterList) {
            var params = this.getTags("param");
            if (params.length == 0 && this.params && this.params.length > 0) {
                params = this.params;
            }
            this.parameterList = params.map(function(p) {
                var words = p.split(" ");
                var type = words[0].match(/^{(\S+)}$/);
                type = type && type[1];
                var pname = type ? words[1] : words[0];
                var desc = words.slice(type ? 2 : 1).join(" ");
                return {type: type, name: pname, desc: desc};
            });
        }
        return this.parameterList;
    },
    getParameterNames: function() {
        if (this.parameterNames == null) {
            var buffer = new Buffer();
            var params = this.getParameterList();
            for (var i = 0; i < params.length; i++) {
                if (i > 0) buffer.write(", ");
                buffer.write(params[i].name);
            }
            this.parameterNames = buffer.toString();
        }
        return this.parameterNames;
    },
    addTag: function(name, value) {
        this.tags.push([name, value]);
    }
};

var nodeToString = function(node) {
    if (node.type == Token.GETPROP) {
        return [nodeToString(node.target), node.property.string].join('.');
    } else if (node.type == Token.NAME) {
        return node.string;
    } else if (node.type == Token.STRING) {
        return node.value;
    } else if (node.type == Token.THIS) {
        return "this";
    } else {
        return getTypeName(node);
    }
};

function isGreatGrandMa(parent, child) {
    return parent && child.parent
            && child.parent.parent
            && child.parent.parent.parent == parent;
}

function getNestingLevel(node) {
    var count = 0;
    while (node.parent) {
        count++;
        node = node.parent;
    }
    return count;

}
