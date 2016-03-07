/*global define */
'use strict';

define(function (require, exports) {
    var delimiter = '.',
        getBase,
        getExt,
        getName;

    getBase = exports.getBase = function (file) {
        var ext = file.name.substr(file.name.lastIndexOf('.') + 1);
        var name = file.name.substr(0, file.name.length-(ext.length+1));
        var parts = [name, ext];
        if (parts) {
            return parts;
        }
        return null;
    };

    getExt = exports.getExt = function (file) {
        var parts = getBase(file), ext = null;

        if (parts.length > 1) {
            ext = parts[parts.length - 1].toLowerCase();
        }
        return ext;
    };


    getName = exports.getName = function (file) {
        var parts = getBase(file);

        if (parts.length > 1) {
            if (getExt(file) === 'xml' && parts[0].endsWith('.shp')) {
                parts[0] = parts[0].replace('.shp', '');
            }
            parts.splice(parts.length - 1);
            return parts.join('.');
        }
        return parts[0];
    };

});
