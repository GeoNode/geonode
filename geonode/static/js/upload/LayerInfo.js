/*global define: true, gn:true, $:true, FormData: true */

define(['jquery', 'underscore', './FileTypes'], function($, _, fileTypes, upload){
    'use strict';

    /** Creates an instance of a LayerInfo
     *  @constructor
     *  @author Ivan Willig
     *  @this {LayerInfo}
     *  @param {name, files}
     */
    var LayerInfo = function (options) {

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

    LayerInfo.prototype.markSuccess = function (resp) {
        var self = this;

        $.ajax({
            url: resp.redirect_to
        }).done(function (resp) {
            var status = self.element.find('#status'), a;
            if (resp.success) {
                status.empty();
                // At this point we need access to the host name
                // Not sure the best way to access
                status.append(self.successTemplate({
                    name: resp.name
                }));
            } else {
                status.empty();
                status.append(self.progressTemplate({
                    alertLevel: 'alert-error',
                    message: 'There was an error in uploading your file, ' + resp.errors.join(', ')
                }));
            }
        });

    };

    LayerInfo.prototype.markStart = function () {

        this.element.find('#status').append(
            this.progressTemplate({
                message: 'Your upload has started.',
                alertLevel: 'alert-success'
            })
        );
    };

    LayerInfo.prototype.uploadFiles = function () {
        var form_data = this.prepareFormData(),
            self = this;

        $.ajax({
            url: "",
            type: "POST",
            data: form_data,
            processData: false, // make sure that jquery does not process the form data
            contentType: false,
            beforeSend: function () {
                self.markStart();
            }
        }).done(function (resp) {
            var status, msg;
            if (resp.success === true) {
                self.markSuccess(resp);
            } else {
                status = self.element.find('#status');
                console.log(status);
            }
        });
    };

    LayerInfo.prototype.display  = function (file_queue) {
        var layerTemplate =_.template($('#layerTemplate').html());

        var li = layerTemplate({
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
    /*
     * @returns {array}
     */

    //TODO use regex to get filename parts

    LayerInfo.getBase = function (file) {
        return file.name.match(/(\w+)\.(\w+)/);
    };

    LayerInfo.getExt = function (file) {
        var parts = LayerInfo.getBase(file);
        return parts[parts.length - 1];
    };

    LayerInfo.getName = function (file) {
        return LayerInfo.getBase(file)[1];
    };

    return LayerInfo;

});
