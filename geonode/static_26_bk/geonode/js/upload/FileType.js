/*global define: true, $:true */
'use strict';

define(function (require, exports) {
    var getExt = require('upload/path').getExt,
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


    FileType.prototype.isType = function (file) {
        return (this.main === getExt(file));
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




