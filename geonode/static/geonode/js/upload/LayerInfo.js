/*jslint nomen: true */
/*global define:true, $:true, FormData: true, alert: true, window:true */
'use strict';

define(function (require, exports) {

    var $        = require('jquery'),
        _        = require('underscore'),
        fileTypes = require('upload/FileTypes'),
        path     = require('upload/path'),
        common     = require('upload/common'),
        LayerInfo;

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

        // need to find a way converting this name to a safe selector
        this.selector = '#' + LayerInfo.safeSelector(this.name) + '-element';

        this.errors = this.collectErrors();
    };

    /** Function to safely select a filename 
     *
     *  @params name 
     *  @returns string 
     */
    LayerInfo.safeSelector = function (name) {
        return name.replace(/\[|\]|\(|\)/g, '_');
    };

    /** Function to get progress template 
     *
     *  @params {options}
     *  @returns 
     */
    LayerInfo.prototype.progressTemplate  = function (options) {
        var template =  _.template($('#progressTemplate').html());
        return template(options);
    };

    /** Function to return the success template  
     *
     *  @params {options}
     *  @returns 
     */
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

    /** Function to check the type of a Layer 
     *
     *  @params {options}
     *  @returns {string}
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
     *
     *  @params {options}
     *  @returns {string}
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

    /** Function to get all the file extensions in
     *  the current list of files being handled. 
     *
     *  @params {options}
     *  @returns {string}
     */
    LayerInfo.prototype.getExtensions = function () {
        var files = this.files,
            extension,
            file,
            res = [],
            i;

        for (i = 0; i < files.length; i += 1) {
            file = files[i];
            extension = path.getExt(file);
            res.push(extension);
        }
        return res;
    };

    /** Build a new FormData object from the current state of the
     *  LayerInfo object.
     * 
     *  @returns {FromData}
     */
    LayerInfo.prototype.prepareFormData = function (form_data) {
        var i, ext, file, perm, geogit, time;

        if (!form_data) {
            form_data = new FormData();
        }
        // this should be generate from the permission widget
        if (typeof permissionsString == 'undefined'){
            perm = {}
        }
        else {
            perm = permissionsString($('#permission_form'),'layers');
        }

        if (geogit_enabled) {
            geogit = $('#' + this.main.name.slice(0, -4) + '-geogit').is(':checked');
            form_data.append('geogit', geogit);
        }
        if (time_enabled) {
            time = $('#' + this.main.name.slice(0, -4) + '-time').is(':checked');
            form_data.append('time', time);
        } 

        form_data.append('base_file', this.main);
        form_data.append('permissions', JSON.stringify(perm));

        for (i = 0; i < this.files.length; i += 1) {
            file = this.files[i];
            if (file.name !== this.main.name) {
                ext = path.getExt(file);
                form_data.append(ext + '_file', file);
            }
        }
        return form_data;
    };

    /** Log the status to the status div 
     *
     *  @params {options}
     *  @returns {string}
     */
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

    /** Function to mark errors in the the status 
     *
     *  @params {error}
     *  @returns {string}
     */
    LayerInfo.prototype.markError = function (error, status) {
        this.logStatus({msg: error, level: 'alert-error'});
    };

    /** Function to mark the start of the upload
     *
     *  @params {options}
     *  @returns {string}
     *
     *  TODO: make this into an abstract method so we can mark events in a
     *  more generic way
     */
    LayerInfo.prototype.markStart = function () {
        this.logStatus({
            msg: 'Your upload has started',
            level: 'alert-success'
        });
    };
   
    LayerInfo.prototype.doResume = function (event) {
        common.make_request({
            url: event.data.url,
            async: false,
            failure: function (resp, status) {
                self.markError(resp.errors, status);
            },
            success: function (resp, status) {
                window.location = resp.redirect_to; 
            },
        });
        return false;
    };

    LayerInfo.prototype.displayUploadedLayerLinks = function(resp) {
        var self = this;
        var a = '<a href="' + resp.url + '" class="btn">Layer Info</a>';
        var b = '<a href="' + resp.url + '/metadata" class="btn">Metadata</a>';
        self.logStatus({
            msg: '<p> Your layer was successful uploaded<br/><br/>' + a + '&nbsp;&nbsp;&nbsp;' + b + '.</p>',
            level: 'alert-success'
        });
    };
 
    /** Function to deal with the final step in the upload process 
     *
     *  @params {options}
     *  @returns {string}
     */
    LayerInfo.prototype.doFinal = function (resp) {
        var self = this;
        if (resp.redirect_to === '/upload/final') {
            common.make_request({
                url: resp.redirect_to,
                async: false,
                failure: function (resp, status) {
                    self.markError(resp.errors, status); 
                },
                success: function (resp, status) {
                    if (resp.status === "other") {
                        self.logStatus({
                            msg:'<p>You need to specify more information in order to complete your upload</p>',
                            level: 'alert-success'
                        });
                    } else {
                        self.displayUploadedLayerLinks(resp);
                    }
                },
            });
        } else if (resp.status === "incomplete") {
            var a = '<a id="next_step">Layer Upload</a>';
            self.logStatus({
                msg:'<p>You need to specify more information in order to complete your upload. You can continue your ' + a + '.</p>',
                level: 'alert-success'
            });
            $("#next_step").on('click', resp, self.doResume);
            return;
        } else if (resp.status === "other") {
            self.logStatus({
                msg:'<p>You need to specify more information in order to complete your upload</p>',
                level: 'alert-success'
            });
        } else if (resp.success === true) {
            self.displayUploadedLayerLinks(resp);
        } else {
            self.logStatus({
                msg:'<p>Unexpected Error</p>',
                level: 'alert-error'
            });
        }

    };

    /** Function to deal with the Steps in the upload process
     *
     *  @params {options}
     *  @returns {string}
     */
    LayerInfo.prototype.doStep = function (resp) {
        var self = this;
        if (resp.success === true && resp.status === 'incomplete') {
            common.make_request({
                url: resp.redirect_to + '?force_ajax=true',
                async: false,
                failure: function (resp, status) {
                    self.markError(resp.errors, status);
                },
                success: function (resp, status) {
                    if (resp.status === 'incomplete') {
                        if (resp.input_required === true) {
                            self.doFinal(resp);
                        } else {
                            self.doStep(resp);
                        }
                    } else if (resp.redirect_to === '/upload/final') {
                        self.doFinal(resp);
                    }
                }
            });
        } else if (resp.success === true && typeof resp.url != 'undefined') {
            self.doFinal(resp);
        } else if (resp.success === true && resp.redirect_to === '/upload/final') {
            self.doFinal(resp);
        }
    };

    /** Function to upload the files against the specified endpoint
     *
     *  @params
     *  @returns
     */
    LayerInfo.prototype.uploadFiles = function () {
        var form_data = this.prepareFormData(),
            self = this;
        $.ajax({
            url: form_target,
            async: false,
            type: "POST",
            data: form_data,
            processData: false,
            contentType: false,
            beforeSend: function () { self.markStart(); },
            error: function (jqXHR) {
                if (jqXHR === null) {
                    self.markError("Unexpected Error");
                } else {
                    self.markError($.parseJSON(jqXHR.responseText).errors);
                }
            },
            success: function (resp, status) {
                self.doStep(resp); 
            }
        });
    };

    /** Function to display the layers collected from the files
     * selected for uploading 
     *
     *  @params {file_queue}
     *  @returns {string}
     */
    LayerInfo.prototype.display = function (file_queue) {
        console.log(geogit_enabled, time_enabled);
        var layerTemplate = _.template($('#layerTemplate').html()),
            li = layerTemplate({
                name: this.name,
                selector: LayerInfo.safeSelector(this.name),
                type: this.type.name,
                geogit_enabled: geogit_enabled,
                time_enabled: time_enabled,
            });
        file_queue.append(li);
        this.errors = this.collectErrors();
        this.displayFiles();
        this.displayErrors();
        this.element = $(this.selector);
        return li;
    };

    /** Event handler to deal with user clicking on remove link 
     *
     *  @params event
     *  @returns none 
     */
    LayerInfo.prototype.removeFileHandler = function (event) {
        var target = $(event.target),
            layer_info,
            layer_name = target.data('layer'),
            file_name  = target.data('file');
        this.removeFile(file_name);
        this.displayRefresh();
    };

    /** Function to remove a file from the file list
     *
     *  @params {options}
     *  @returns {string}
     */
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

    /** Function to display the files selected for uploading 
     *
     *  @params
     *  @returns
     */
    LayerInfo.prototype.displayFiles = function () {
        var self = this,
            ul = $('#' + LayerInfo.safeSelector(this.name) + '-element .files');

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

    /** Function to display errors 
     *
     *  @params 
     *  @returns 
     */
    LayerInfo.prototype.displayErrors = function () {
        var ul = $('#' + LayerInfo.safeSelector(this.name) + '-element .errors').first();
        ul.empty();

        $.each(this.errors, function (idx, error) {
            var li = $('<li/>', {text: error, 'class': 'alert alert-error'});
            li.appendTo(ul);
            li.animate({opacity:1}, 5000, 'linear', function() { 
                li.animate({opacity:0}, 1000, 'linear', function() {li.remove(); }); 
            });
        });
    };

    /** Function to refresh display after adding or removing files 
     *
     *  @params {options}
     *  @returns {string}
     */
    LayerInfo.prototype.displayRefresh = function () {
        this.errors = this.collectErrors();
        this.displayFiles();
        this.displayErrors();
    };

    return LayerInfo;
});
