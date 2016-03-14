/*jslint nomen: true */
/*global define:true, $:true, FormData: true, alert: true, window:true */
'use strict';

define(function (require, exports) {

    var _        = require('underscore'),
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
        this.selector = this.selector.replace(' ','_');
        this.name = this.name.replace(' ','_');
        this.errors = this.collectErrors();
        this.polling = false;
    };

    /** Function to safely select a filename
     *
     *  @params name
     *  @returns string
     */
    LayerInfo.safeSelector = function (name) {
        return name.replace(/\[|\]|\(|\)/g, '_');
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
        var i, ext, file, perm, geogig, geogig_store, time;

        if (!form_data) {
            form_data = new FormData();
        }
        // this should be generate from the permission widget
        if (typeof permissionsString == 'undefined'){
            perm = {}
        }
        else {
            perm = permissionsString('#permission_form','layers');
        }

        if (geogig_enabled) {
            geogig = $('#' + this.main.name.slice(0, -4) + '\\:geogig_toggle').is(':checked');
            if (geogig) {
                geogig_store = $('#' + this.main.name.slice(0, -4) + '\\:geogig_store').val();
                form_data.append('geogig_store', geogig_store);
            } else {
                form_data.append('geogig_store', "");
            }
            form_data.append('geogig', geogig);
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

        form_data.append('charset', $('#charset').val());

        // Include captcha
        // form_data.append('g-recaptcha-response',  JSON.stringify(grecaptcha.getResponse()));
        // form_data.append('captcha',  JSON.stringify(grecaptcha.getResponse());
        // console.log(form_data);
        // console.log(JSON.stringify(grecaptcha.getResponse()));
        return form_data;
    };

    /** Log the status to the status div
     *
     *  @params {options}
     *  @returns {string}
     */
    LayerInfo.prototype.logStatus = function (options) {
        options.element = this.element.find('#status');
        common.logStatus(options);
    };

    /** Function to mark errors in the the status
     *
     *  @params {error}
     *  @returns {string}
     */
    LayerInfo.prototype.markError = function (error, status) {
        common.logError(error, this.element.find('#status'));
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
            msg: 'Your upload has started<div class="progress" id="prog"><div class="progress-bar progress-bar-success" style="width:0%"></div>',
            level: 'alert-success',
            empty: 'true'
        });
    };

    LayerInfo.prototype.doResume = function (event) {
        common.make_request({
            url: event.data.url,
            async: true,
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
        var a = '<a href="' + resp.url + '" class="btn btn-success">' + gettext('Layer Info') + '</a>';
        var b = '<a href="' + resp.url + '/metadata" class="btn btn-warning">' + gettext('Edit Metadata') + '</a>';
        var c = '<a href="' + resp.url.replace(/^\/layers/, '/gs') + '/style/manage" class="btn btn-warning">' + gettext('Manage Styles') + '</a>';
        self.logStatus({
            msg: '<p>' + gettext('Your layer was successfully uploaded') + '<br/><br/>' + a + '&nbsp;&nbsp;&nbsp;' + b + '&nbsp;&nbsp;&nbsp;' + c + '</p>',
            level: 'alert-success',
            empty: 'true'
        });
    };

    LayerInfo.prototype.startPolling = function() {
        var self = this;
        if (self.polling) {
            $.ajax({ url: "/upload/progress", type: 'GET', success: function(data){
                // TODO: Not sure we need to do anything here?
                //console.log('polling');
            }, dataType: "json", complete: setTimeout(function() {self.startPolling()}, 3000), timeout: 30000 });
        }
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
                async: true,
                beforeSend: function() {
                    self.logStatus({
                        msg: '<p>' + gettext('Performing Final GeoServer Config Step') + '<img class="pull-right" src="/static/geonode/img/loading.gif"></p>',
                        level: 'alert-success',
                        empty: 'true'
                    });
                    self.polling = true;
                    self.startPolling();
                },
                failure: function (resp, status) {
                    self.polling = false;
                    self.markError(resp.errors, status);
                },
                success: function (resp, status) {
                    self.polling = false;
                    if (resp.status === "other") {
                        self.logStatus({
                            msg:'<p>' + gettext('You need to specify more information in order to complete your upload') + '</p>',
                            level: 'alert-success',
                            empty: 'true'
                        });
                    } else if (resp.status === "pending") {
                        setTimeout(function() {
                            self.doFinal(resp);
                        }, 5000);
                    } else {
                        self.displayUploadedLayerLinks(resp);
                    }
                }
            });
        } else if (resp.status === "incomplete") {
            var id = resp.url.split('=')[1]
            var element = 'next_step_' + id
            var a = '<a id="' + element + '" class="btn">Continue</a>';
            self.logStatus({
                msg:'<p>' + gettext('You need to specify more information in order to complete your upload.') + '</p><p>' + gettext('You can continue configuring your layer.') + '</p><p>' + a + '</p>',
                level: 'alert-success',
                empty: 'true'
            });
            $("#" + element).on('click', resp, self.doResume);
            return;
        } else if (resp.status === "other") {
            self.logStatus({
                msg:'<p>' + gettext('You need to specify more information in order to complete your upload') + '</p>',
                level: 'alert-success',
                empty: 'true'
            });
        } else if (resp.success === true) {
            self.polling = false;
            self.displayUploadedLayerLinks(resp);
        } else {
            self.polling = false;
            self.logStatus({
                msg:'<p>' + gettext('Unexpected Error') + '</p>',
                level: 'alert-error',
                empty: 'true'
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
        self.logStatus({
            msg: '<p>' + gettext('Performing GeoServer Config Step') + '</p>',
            level: 'alert-success',
            empty: 'true'
        });
        if (resp.success === true && resp.status === 'incomplete') {
            common.make_request({
                url: resp.redirect_to + '?force_ajax=true',
                async: true,
                failure: function (resp, status) {
                    self.polling = false;
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
                    } else {
                        window.location = resp.url;
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
        console.log('hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh');
        var form_data = this.prepareFormData(),
            self = this;
        console.log(form_data);
        var prog = "";
        $.ajaxQueue({
            url: form_target,
            async: true,
            type: "POST",
            data: form_data,
            processData: false,
            contentType: false,
            xhr: function() {
                var req = $.ajaxSettings.xhr();
                if (req) {
                    req.upload.addEventListener('progress', function(evt) {
                        if(evt.lengthComputable) {
                            var pct = (evt.loaded / evt.total) * 100;
                            $('#prog > .progress-bar').css('width', pct.toPrecision(3) + '%');
                        }
                    }, false);
                }
                return req;
            },
            beforeSend: function () {
                self.markStart();
                self.polling = true;
                self.startPolling();
            },
            error: function (jqXHR) {
                self.polling = false;
                if (jqXHR === null) {
                    self.markError(gettext('Unexpected Error'));
                } else {
                    self.markError(jqXHR);
                }
            },
            success: function (resp, status) {
                self.logStatus({
                    msg: '<p>' + gettext('Layer files uploaded, configuring in GeoServer') + '</p>',
                    level: 'alert-success',
                    empty: 'true'
                });
                self.doStep(resp);
            }
        });
    };

    LayerInfo.prototype.setupGeogigDropdown = function(selector){
        function format(item){return item.name;};
        $(selector).select2({
           data: {results:geogig_stores, text:'name'},
           formatSelection: format,
           formatResult: format,
           placeholder: gettext('Select or create a Geogig repository.'),

            id: function(object) {
             return object.name;
           },
            createSearchChoice:function(term, data) {
             if ($(data).filter( function() {
               return this.name.localeCompare(term)===0;
             }).length===0) {
               return {name:term.replace(/[`~!@#$%^&*()|+\-=?;:'",.<>\{\}\[\]\\\/]/gi, '')};
             }
           }
          });


    }

    /** Function to display the layers collected from the files
     * selected for uploading
     *
     *  @params {file_queue}
     *  @returns {string}
     */
    LayerInfo.prototype.display = function (file_queue) {
        var layerTemplate = _.template($('#layerTemplate').html()),
            li = layerTemplate({
                name: this.name,
                selector: LayerInfo.safeSelector(this.name),
                type: this.type.name,
                format: this.type.format,
                geogig: geogig_enabled,
                time: time_enabled
            });
        file_queue.append(li);
        this.errors = this.collectErrors();
        this.displayFiles();
        this.displayErrors();
        this.element = $(this.selector);

        $('#' + this.name + '\\:geogig_toggle').on('change', this.doGeoGigToggle);

        // Add values to the geogig store dropdown and hide.
        this.setupGeogigDropdown($('#' + this.main.name.slice(0, -4) + '\\:geogig_store'));
        $("#s2id_" + this.name + "\\:geogig_store").hide()

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
                a  = $('<a/>', {text: ' ' + gettext('Remove')});

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

    LayerInfo.prototype.doGeoGigToggle = function (event) {
        var target = event.target || event.srcElement;
        var id = target.id;
        var base_name = id.split(':')[0];
        var geogig = $('#' + id.replace(':', '\\:')).is(':checked');
        if (geogig) {
            $('#' + base_name + '\\:geogig_store').show();
            $("#s2id_" + base_name + "\\:geogig_store").show()
        } else {
            $("#s2id_" + base_name + "\\:geogig_store").hide()
            $('#' + base_name + '\\:geogig_store').hide();
        }
    };

    return LayerInfo;
});
