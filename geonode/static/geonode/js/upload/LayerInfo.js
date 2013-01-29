/*jslint nomen: true */
/*global define:true, $:true, FormData: true, alert: true, window:true */
'use strict';

define(['jquery', 'underscore', './FileTypes'], function ($, _, fileTypes, upload) {

    var make_request, LayerInfo;

    /** We have a different notion of success and failure for GeoNode's
     * urls this function allows the user to define two functions, success
     * and failure and have the failure function called when an bad
     * http response is returns and also when there is not success
     * property define in the response.
     */
    make_request = (function () {
        return function (options) {
            var success = options.success,
                failure = options.failure;

            delete options.success;
            delete options.failure;

            $.ajax(options).done(function (resp, status) {
                if (resp.success === true) {
                    success(resp, status);
                } else {
                    failure(resp, status);
                }
            }).fail(failure);
        };
    }());

    /** Creates an instance of a LayerInfo
     *  @constructor
     *  @author Ivan Willig
     *  @this {LayerInfo}
     *  @param {name, files}
     */

    LayerInfo = function (options) {

        this.name     = null;
        this.files    = null;

        this.type     = null;
        this.main     = null;


        this.element  = null;
        $.extend(this, options || {});
        if (!this.main || !this.type) {
            this.guessFileType();
        }
        this.selector = '#' + this.name + '-element';
        this.errors = this.collectErrors();
    };

    LayerInfo.prototype.progressTemplate  = function (options) {
        var template =  _.template($('#progressTemplate').html());
        return template(options);
    };

    LayerInfo.prototype.successTemplate = function (options) {
        var template = _.template($('#successTemplate').html());
        return template(options);
    };

    /* Function to iterates through all of the known types and returns the
     * type if it matches, if not return null
     * @params {File}
     * @returns {object}
     */
    LayerInfo.prototype.findFileType = function (file) {
        var i, type, res;

        $.each(fileTypes, function (name, type) {
            if (type.isType(file)) {
                res = {type: type, file: file};
                return false;
            }
        });
        return res;
    };


    /** Checks the type of the Layer.
     *
     */
    LayerInfo.prototype.guessFileType = function () {
        var self = this;

        $.each(this.files, function (idx, file) {
            var results = self.findFileType(file);
            // if we find the type of the file, we also find the "main"
            // file
            if (results) {
                self.type = results.type;
                self.main = results.file;
            }
        });
    };

    /** Delegates to the Layer Type to find all of the errors
     *  associated with this type.
     */
    LayerInfo.prototype.collectErrors = function () {
        var errors = [];
        if (this.type) {
            errors = this.type.findTypeErrors(this.getExtensions());
        } else {
            errors.push('Unknown type, please try again');
        }
        return errors;
    };

    LayerInfo.prototype.getExtensions = function () {
        var files = this.files,
            extension,
            file,
            res = [],
            i;

        for (i = 0; i < files.length; i += 1) {
            file = files[i];
            extension = LayerInfo.getExt(file);
            res.push(extension);
        }
        return res;
    };

    /** Build a new FormData object from the current state of the
     *  LayerInfo object.
     *  @returns {FromData}
     */
    LayerInfo.prototype.prepareFormData = function (form_data) {
        var i, ext, file, perm;

        if (!form_data) {
            form_data = new FormData();
        }
        // this should be generate from the permission widget
        perm = {users: []};

        form_data.append('base_file', this.main);
        form_data.append('permissions', JSON.stringify(perm));


        for (i = 0; i < this.files.length; i += 1) {
            file = this.files[i];
            if (file.name !== this.main.name) {
                ext = LayerInfo.getExt(file);
                form_data.append(ext + '_file', file);
            }
        }

        return form_data;
    };
    LayerInfo.prototype.logStatus = function (options) {
        var status = this.element.find('#status'),
            empty = options.empty;

        if (empty) {
            status.empty();
        }

        status.append(this.progressTemplate({
            message: options.msg,
            alertLevel: options.level
        }));
    };
    LayerInfo.prototype.markError = function (error) {
        this.logStatus({msg: '[ ' + error + ' ]'});
    };

    // make this into an abstract method so we can mark events in a
    // more generic way

    LayerInfo.prototype.markStart = function () {
        this.logStatus({
            msg: 'Your upload has started',
            level: 'alert-success'
        });
    };

    /*

      We need to add a step for the srs url and then the final

     */
    LayerInfo.prototype.doFinal = function (resp) {
        var self = this;
        make_request({
            url: resp.redirect_to,
            failure: function (resp, status) {self.markError(resp); },
            success: function (resp, status) {
                // hack find a better way of creating a string
                var a = '<a href="' + resp.url + '">Layer page</a>';
                self.logStatus({
                    msg: '<p> Your layer was successful uploaded, please visit the ' + a + ' page </p>',
                    level: 'alert-success'
                });
            },
        });
    };

    LayerInfo.prototype.doSrs = function (resp) {
        // at this point we need to allow the user to select an srs
        var self = this;
        make_request({
            url: resp.redirect_to,
            failure: function (resp, status) { self.markError(resp); },
            success: function (resp, status) { self.doFinal(resp); }
        });
    };

    LayerInfo.prototype.uploadFiles = function () {
        var form_data = this.prepareFormData(),
            self = this;

        $.ajax({
            url: "", // is this right?
            type: "POST",
            data: form_data,
            processData: false, // make sure that jquery does not process the form data
            contentType: false,
            beforeSend: function () {
                self.markStart();
            }
        }).done(function (resp) {
            self.doSrs(resp);
        }).fail(function (resp) {
            alert('Response failed,' + resp.errors);
        });
    };

    LayerInfo.prototype.display  = function (file_queue) {
        var layerTemplate = _.template($('#layerTemplate').html()),
            li = layerTemplate({
                name: this.name,
                type: this.type.name,
            });

        file_queue.append(li);
        this.displayFiles();
        this.displayErrors();
        this.element = $(this.selector);
        return li;
    };

    LayerInfo.prototype.removeFile = function (event) {
        var target = $(event.target),
            layer_info,
            layer_name = target.data('layer'),
            file_name  = target.data('file');

        this.removeFile(file_name);
        this.displayRefresh();


    };

    LayerInfo.prototype.displayFiles = function () {
        var self = this,
            ul = $('#' + this.name + '-element .files');

        ul.empty();

        $.each(this.files, function (idx, file) {
            var li = $('<li/>').appendTo(ul),
                p = $('<p/>', {text: file.name}).appendTo(li),
                a  = $('<a/>', {text: ' Remove'});

            a.data('layer', self.name);
            a.data('file',  file.name);
            a.appendTo(p);
            a.on('click', function (event) {
                var target = $(event.target),
                    layer_info,
                    layer_name = target.data('layer'),
                    file_name  = target.data('file');

                self.removeFile(file_name);
                self.displayRefresh();
            });

        });

    };

    LayerInfo.prototype.displayErrors = function () {
        var ul = $('#' + this.name + '-element .errors').first();
        ul.empty();

        $.each(this.errors, function (idx, error) {
            $('<li/>', {text: error, 'class': 'alert alert-error'}).appendTo(ul);
        });
    };

    LayerInfo.prototype.displayRefresh = function () {

        this.errors = this.collectErrors();
        this.displayFiles();
        this.displayErrors();
    };

    LayerInfo.prototype.removeFile = function (name) {
        var length = this.files.length,
            i,
            file;

        for (i = 0; i < length; i += 1) {
            file = this.files[i];
            if (name === file.name) {
                this.files.splice(i, 1);
                break;
            }
        }

    };


    /**
     * @returns {array}
     */
    LayerInfo.getBase = function (file) {
        var parts = file.name.split('.');

        if (parts) {
            return parts;
        }

        return null;
    };

    LayerInfo.getExt = function (file) {
        var parts = LayerInfo.getBase(file), ext = null;

        if (parts) {
            ext = parts[parts.length - 1].toLowerCase();
        }
        return ext;
    };

    LayerInfo.getName = function (file) {
        var parts = LayerInfo.getBase(file);

        if (parts.length > 1) {
            parts.splice(parts.length - 1);
            return parts.join('.');
        }
        return parts[0];
    };

    return LayerInfo;

});
