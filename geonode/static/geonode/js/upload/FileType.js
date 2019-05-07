/*global define: true, $:true */
'use strict';

define(function (require, exports) {
    var getExt = require('./path').getExt,
        FileType;

    /** Create an instance of a FileType object
     *  @constructor
     *  @author Ivan Willig
     *  @this {FileType}
     *  @param {name, main, requires}
     */

    FileType = function (options) {
        this.name = null;
        this.main = null;
        this.requires = !('requires' in options) ? [options.main] : null;
        $.extend(this, options || {});
    };


    FileType.prototype.isType = function (file, extensions) {
        var main_matches = (this.main === getExt(file));
        var aux_matches = this.findAuxiliaryFiles(extensions);
        return main_matches && aux_matches;
    };

    FileType.prototype.findAuxiliaryFiles = function (extensions) {
        if (this.aux === undefined || this.aux === null || this.aux.length === 0) {
            return true;
        }

        var matches = false;
        $.each(this.aux, function (idx, req) {
            idx = $.inArray(req, extensions);
            if (idx !== -1) {
                matches = true;
            }
        });
        return matches;
    };

    FileType.prototype.findTypeErrors = function (extensions) {
        var errors = [];

        $.each(this.requires, function (idx, req) {
            idx = $.inArray(req, extensions);
            if (idx === -1) {
                errors.push(interpolate(gettext('Missing a %s file, which is required'),[req]));
            }
        });
        return errors;
    };

    return FileType;

});
