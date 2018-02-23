/**
 * @fileoverview <p>This module provides the RingoJS-specific global functions
 * import, include, and export, as well as require.loader for Narwhal
 * compatibility.</p>
 */

Object.defineProperty(this, "global", { value: this });

(function() {

    /**
     * Load a module and include all its properties in the calling scope.
     * @param {String} moduleName the module name such as 'core.object'
     */
    Object.defineProperty(this, "include", {
        value: function(moduleName) {
            var module = this.require(moduleName);
            for (var key in module) {
                this[key] = module[key];
            }
        }
    });

    /**
     * Define the properties to be exported.
     * @param name one or more names of exported properties
     */
    Object.defineProperty(this, "export", {
        value: function() {
            var module = this;
            var exports = this.exports;
            if (!exports || typeof exports != "object") {
                // this should never happen with ringo modules
                exports = {};
                Object.defineProperty(module, "exports", { value: exports });
            }
            Array.forEach(arguments, function(name) {
                Object.defineProperty(exports, name, {
                    get: function() {
                        return module[name];
                    },
                    enumerable: true
                });
            });
        }
    });

    // preload system module
    var system = this.system = this.system || require('system');

    // Firebug-like debug console
    Object.defineProperty(this, "console", {
        get: function() require("console"),
        enumerable: true
    });

    // Include file and line number in error.toString() - better error messages ftw!
    Object.defineProperty(Error.prototype, "toString", {
        value: function() {
            if (this.fileName && this.lineNumber != null) {
                return [
                    this.name, ": ",
                    this.message, " (",
                    this.fileName, "#",
                    this.lineNumber, ")"].join("");
            }
            return this.name + ": " + this.message;
        },
        writable: true, configurable: true
    });

})(global);
