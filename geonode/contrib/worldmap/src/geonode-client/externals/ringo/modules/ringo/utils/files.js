/**
 * @fileOverview A collection of file related utilities.
 */

var arrays = require('ringo/utils/arrays');
var fs = require('fs');

export ('resolveUri', 'resolveId', 'isHidden', 'createTempFile', 'roots', 'separator');

var File = java.io.File;

/**
 * Resolve an arbitrary number of path elements relative to each other.
 * This is an adapted version of the file module's resolve function that always
 * and strictly uses forward slashes as file separators. This makes it
 * usable for resolving URI paths as well as module ids and resource paths.
 * Originally adapted for helma/file from narwhal's file module.
 * @param {...} arbitrary number of path elements
 */
function resolveUri() {
    var root = '';
    var elements = [];
    var leaf = '';
    var path;
    var SEPARATOR = '/';
    var SEPARATOR_RE = /\//;
    for (var i = 0; i < arguments.length; i++) {
        path = String(arguments[i]);
        if (path.trim() == '') {
            continue;
        }
        var parts = path.split(SEPARATOR_RE);
        if (path[0] == '/') {
            // path is absolute, throw away everyting we have so far
            root = parts.shift() + SEPARATOR;
            elements = [];
        }
        leaf = parts.pop();
        if (leaf == '.' || leaf == '..') {
            parts.push(leaf);
            leaf = '';
        }
        for (var j = 0; j < parts.length; j++) {
            var part = parts[j];
            if (part == '..') {
                if (elements.length > 0 && arrays.peek(elements) != '..') {
                    elements.pop();
                } else if (!root) {
                    elements.push(part);
                }
            } else if (part != '' && part != '.') {
                elements.push(part);
            }
        }
    }
    path = elements.join(SEPARATOR);
    if (path.length > 0) {
        leaf = SEPARATOR + leaf;
    }
    return root + path + leaf;
}

/**
 * Resolve path fragment child relative to parent but only
 * if child is a a relative path according to the CommonJS Modules
 * spec, i.e. starts with "." or "..". Otherwise, the child path
 * is returned unchanged.
 *
 * @param {String} parent the parent path
 * @param {String} child the child path
 */
function resolveId(parent, child) {
    // only paths starting with "." or ".." are relative according to module spec
    var path = child.split("/");
    if (path[0] == "." || path[0] == "..") {
        // we support absolute paths for module ids. Since absolute
        // paths are platform dependent, use the file module's version
        // of resolve() for these instead of resolveUri().
        return fs.isAbsolute(parent) ?
               fs.resolve(parent, child) : resolveUri(parent, child);
    }
    // child is not relative according to module spec, return it as-is
    return child;
}

/**
 * Create a new empty temporary file in the default directory for temporary files.
 * @param {String} prefix the prefix of the temporary file; must be at least three characters long
 * @param {String} suffix the suffix of the temporary file; may be undefined or null
 * @param {String} directory optional directory in which to create the file. Pass undefined
 *                 to use the system's default location for temporary files
 * @returns {File} the temporary file
 */
function createTempFile(prefix, suffix, directory) {
    suffix = suffix || null;
    directory = directory ? new File(directory) : null;
    return File
        .createTempFile(prefix, suffix, directory)
        .getPath();
}

/**
 * Tests whether the file represented by this File object is a hidden file.
 * What constitutes a hidden file may depend on the platform we are running on.
 * @param {String} file
 * @returns Boolean true if this File object is hidden
 * @type Boolean
 */
function isHidden(file) {
    return new File(file).isHidden();
}

/**
 * An Array containing the system's file system roots. On UNIX platforms
 * this contains a single "/" directory, while on Windows platforms this
 * contains an element for each mounted drive.
 * @type Array
 */
var roots = File.listRoots().map(String);

/**
 * The system-dependent file system separator character.
 * @type String
 */
var separator = File.separator;
