/*global define */
'use strict';

define(function (require, exports) {
    var delimiter = '.',
        getBase,
        getExt,
        getName;

    getBase = exports.getBase = function (file) {
        var parts = file.name.split(delimiter);
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
            if (getExt(file) === 'xml' && 
                    parts[parts.length - 2].toLowerCase() === 'shp'){               
                parts.pop(); 
            }
            parts.splice(parts.length - 1);
            return parts.join('.');
        }
        return parts[0];
    };

});
