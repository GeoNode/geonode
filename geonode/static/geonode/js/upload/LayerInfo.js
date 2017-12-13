/*jslint nomen: true */
/*global define:true, $:true, FormData: true, alert: true, window:true */
'use strict';

define(function (require, exports) {

        var _      = require('underscore'),
        fileTypes  = require('upload/FileTypes'),
        path       = require('upload/path'),
        common     = require('upload/common'),
        LayerInfo;

    /** Creates an instance of a LayerInfo
     *  @constructor
     *  @author Ivan Willig
     *  @this {LayerInfo}
     *  @param {name, files}
     */
    LayerInfo = function (options) {

        this.id       = null;
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
        this.name = LayerInfo.safeSelector(this.name.split('.')[0]);
        this.selector = '#' + this.name + '-element';
        this.errors = this.collectErrors();
        this.polling = false;
    };

    /** Function to safely select a filename
     *
     *  @params name
     *  @returns string
     */
    LayerInfo.safeSelector = function (name) {
        return name.replace(/\[|\]|\(|\)| /g, '_');
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
                // Avoid assuming the metadata file as main one
                if (results.type.main == 'xml' && self.main != undefined) {
                   self.type = self.type;
                   self.main = self.main;
                } else {
                   self.type = results.type;
                   self.main = results.file;
                }
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
        var mosaic_is_valid = true;
        var is_granule = $('#' + this.name + '-mosaic').is(':checked');

        var is_time_enabled = $('#' + this.name + '-timedim').is(':checked');
	    var is_time_valid = is_time_enabled && !$('#' + this.name + '-timedim-value-valid').is(':visible');

        if (is_granule && is_time_enabled) {
		    mosaic_is_valid = is_time_valid;
	    }
	    if (is_granule && !mosaic_is_valid) {
		    errors.push('The configuration of the file as a Mosaic Granule is not valid, please fix the issue and try again');
	    }

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
        var i, ext, file, perm, geogig, geogig_store, time, mosaic;

        var base_ext  = this.main.name.split('.').pop();
        var base_name = this.name;

        var base_ext  = this.main.name.split('.').pop();
        var base_name = this.name;

        var base_ext  = this.main.name.split('.').pop();
        var base_name = this.name;

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
            geogig_store = $('#' + base_name + '\\:geogig_store').val();
            geogig = $('#' + base_name + '\\:geogig_toggle').is(':checked') && geogig_store.length != 0;
            if (geogig) {
                form_data.append('geogig_store', geogig_store);
            } else {
                form_data.append('geogig_store', "");
            }
            form_data.append('geogig', geogig);
        }
        if (time_enabled) {
            time = (this.type && (this.type.main === 'shp' || this.type.main === 'csv'));
            form_data.append('time', time);
        }
        if (mosaic_enabled) {
            mosaic = $('#' + base_name + '-mosaic').is(':checked');
			var is_time_valid = $('#' + base_name + '-timedim').is(':checked') && !$('#' + base_name + '-timedim-value-valid').is(':visible');

			if (mosaic /*&& is_time_valid*/) {
				form_data.append('mosaic', mosaic);

				var append_to_mosaic_opts = $('#' + base_name + '-mosaic-granule').is(':checked');
				var append_to_mosaic_name = $('#' + base_name + '-mosaic-granule-format-select').val();

				//console.log("append_to_mosaic_opts:" + append_to_mosaic_opts + " / append_to_mosaic_name:" + append_to_mosaic_name);

                if (is_time_valid) {
                    var time_regex = $('#' + base_name + '-timedim-format-select').val();
                    var time_value = $('#' + base_name + '-timedim-value').val();

                    //console.log("time_regex:" + time_regex + " / time_value:" + time_value);

                    var time_presentation_opts = $('#' + base_name + '-timedim-presentation').is(':checked');
                    var time_presentation = "LIST";
                    var time_presentation_res = 0;
                    var time_presentation_default_value = "";
                    var time_presentation_reference_value = "";
                    if (time_presentation_opts) {
                        time_presentation = $('#' + base_name + '-timedim-presentation-format-select').val();

                        if (time_presentation === 'DISCRETE_INTERVAL') {
                            // Years
                            time_presentation_res += parseInt( $('#' + base_name + '-timedim-presentation-years').val() ) * 31536000000;
                            // Months
                            time_presentation_res += parseInt( $('#' + base_name + '-timedim-presentation-months').val() ) * 2628000000;
                            // Weeks
                            time_presentation_res += parseInt( $('#' + base_name + '-timedim-presentation-weeks').val() ) * 604800000;
                            // Days
                            time_presentation_res += parseInt( $('#' + base_name + '-timedim-presentation-days').val() ) * 86400000;
                            // Hours
                            time_presentation_res += parseInt( $('#' + base_name + '-timedim-presentation-hours').val() ) * 3600000;
                            // Minutes
                            time_presentation_res += parseInt( $('#' + base_name + '-timedim-presentation-minutes').val() ) * 60000;
                            // Seconds
                            time_presentation_res += parseInt( $('#' + base_name + '-timedim-presentation-seconds').val() ) * 1000;
                        }

                        time_presentation_default_value = $('#' + base_name + '-timedim-defaultvalue-format-select').val();

                        if (time_presentation_default_value == 'NEAREST' || time_presentation_default_value == 'FIXED') {
                            time_presentation_reference_value = $('#' + base_name + '-timedim-defaultvalue-ref-value').val();
                        }
                    }

                    //console.log("time_presentation:" + time_presentation + " / time_presentation_res:" + time_presentation_res);

                    form_data.append('mosaic_time_regex', time_regex);
                    form_data.append('mosaic_time_value', time_value);

                    form_data.append('time_presentation', time_presentation);
                    form_data.append('time_presentation_res', time_presentation_res);

                    form_data.append('time_presentation_default_value', time_presentation_default_value);
                    form_data.append('time_presentation_reference_value', time_presentation_reference_value);
                }

				form_data.append('append_to_mosaic_opts', append_to_mosaic_opts);
				if (append_to_mosaic_opts) {
					form_data.append('append_to_mosaic_name', append_to_mosaic_name);
				}
			}
        }

        form_data.append('base_file', this.main);
        form_data.append('permissions', JSON.stringify(perm));

        for (i = 0; i < this.files.length; i += 1) {
            file = this.files[i];
            if (file.name !== this.name) {
                ext = path.getExt(file);
                form_data.append(ext + '_file', file);
            }
        }

        form_data.append('charset', $('#charset').val());
        if ($('#id_metadata_upload_form').prop('checked')) {
             form_data.append('metadata_upload_form', true);
        }
        if ($('#id_metadata_uploaded_preserve').prop('checked')) {
             form_data.append('metadata_uploaded_preserve', true);
        }
        if ($('#id_style_upload_form').prop('checked')) {
             form_data.append('style_upload_form', true);
             form_data.append('layer_title', $('#id_layer_title').val());
        }
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
        var error = (error != undefined ? error : 'Unespected error!');
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
                if (resp && resp.errors) {
                    self.markError(resp.errors, status);
                } else {
                    self.markError(gettext('Unexpected Error'), status);
                }
            },
            success: function (resp, status) {
                if(resp.url && resp.input_required){
                    window.location = resp.url;
                }else {
                    window.location = resp.redirect_to;
                }
            },
        });
        return false;
    };

    LayerInfo.prototype.displayUploadedLayerLinks = function(resp) {
        var self = this;
        var a = '<a href="' + resp.url + '" class="btn btn-success">' + gettext('Layer Info') + '</a>';
        var b = '<a href="' + resp.url + '/metadata" class="btn btn-warning">' + gettext('Edit Metadata') + '</a>';
        var c = '<a href="' + resp.url + '/metadata_upload" class="btn btn-warning">' + gettext('Upload Metadata') + '</a>';
        var d = '<a href="' + resp.url + '/style_upload" class="btn btn-warning">' + gettext('Upload SLD') + '</a>';
        var e = '<a href="' + resp.url.replace(/^\/layers/, '/gs') + '/style/manage" class="btn btn-warning">' + gettext('Manage Styles') + '</a>';
        if(resp.ogc_backend == 'geonode.qgis_server'){
            // QGIS Server has no manage style interaction.
            d = '';
        }
        var msg_col = "";
        if (resp.info){
            var msg_template = gettext('The column %1 was renamed to %2 <br/>');
            for (var key in resp.info){
               msg_col += format(msg_template,[key,resp.info[key]]);
            }
        }
        self.logStatus({
            msg: '<p>' + gettext('Your layer was successfully uploaded') + '<br/>' + msg_col + '<br/>' + a + '&nbsp;&nbsp;&nbsp;' + b + '&nbsp;&nbsp;&nbsp;' + c + '&nbsp;&nbsp;&nbsp;' + d + '&nbsp;&nbsp;&nbsp;' + e + '</p>',
            level: 'alert-success',
            empty: 'true'
        });
    };

    LayerInfo.prototype.startPolling = function() {
        var self = this;
        if (self.polling) {
            $.ajax({ url: updateUrl("/upload/progress", 'id', self.id), type: 'GET', success: function(data){
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
        if (resp.hasOwnProperty('redirect_to') && resp.redirect_to.indexOf('/upload/final') > -1) {
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
                    } else if (resp.status === 'error') {
                        self.polling = false;
                        self.markError(resp.error_msg, resp.status);
                    } else {
                        self.displayUploadedLayerLinks(resp);
                    }
                }
            });
        } else if (resp.status === "incomplete") {
            var id = common.parseQueryString(resp.url).id;
            var element = 'next_step_' + id
            var a = '<a id="' + element + '" class="btn btn-primary" target="_new">Continue</a>';
            var msg = '<p>' + gettext('Files are ready to be ingested!')

            if (resp.redirect_to.indexOf('time') !== -1 || resp.url.indexOf('time') !== -1) {
                msg += '&nbsp;' + gettext('A temporal dimension may be added to this Layer.') + '&nbsp;' + a + '</p>'
            } else {
                msg += '&nbsp;' + a + '</p>'
            }

            self.logStatus({
                msg: msg,
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
        } else if (resp.status === 'error') {
            self.polling = false;
            self.markError(resp.error_msg, resp.status);
        } else if (resp.success === true) {
            self.polling = false;
            self.displayUploadedLayerLinks(resp);
        } else {
            self.polling = false;
            resp.errors = 'Unexpected Error';
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
                url: updateUrl(resp.redirect_to, 'force_ajax', 'true'),
                async: true,
                failure: function (resp, status) {
                    self.polling = false;
                    if (resp.status && resp.status !== 'success') {
                        self.markError(resp.error_msg, resp.status);
                    } else {
                        self.markError(resp.errors, status);
                    }
                },
                success: function (resp, status) {
                    self.id = resp.id;
                    if (resp.status === 'incomplete') {
                        if (resp.input_required === true) {
                            self.doFinal(resp);
                        } else {
                            self.doStep(resp);
                        }
                    } else if (resp.status === 'error') {
                        self.polling = false;
                        self.markError(resp.error_msg, resp.status);
                    } else if (resp.redirect_to.indexOf('/upload/final') > -1) {
                        self.doFinal(resp);
                    } else {
                        window.location = resp.url;
                    }
                }
            });
        } else if (resp.success === true && resp.status === 'error') {
            self.polling = false;
            self.markError(resp.error_msg, resp.status);
        } else if (resp.success === true && typeof resp.url != 'undefined') {
            self.doFinal(resp);
        } else if (resp.success === true && resp.redirect_to.indexOf('/upload/final') > -1) {
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
                self.id = resp.id;
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
                time: time_enabled,
				mosaic: mosaic_enabled
            });
        file_queue.append(li);
        this.errors = this.collectErrors();
        this.displayFiles();
        this.displayErrors();
        this.element = $(this.selector);

	    var time_re_txt = "[0-9]{8}";

        $('#' + this.name + '-mosaic').on('change', this.doImageMosaicToggle);
        $('#' + this.name + '-mosaic-granule').on('change', this.doImageMosaicGranuleOptionsToggle);
        $('#' + this.name + '-timedim').on('change', this.doImageMosaicTimedimOptionsToggle);
        $('#' + this.name + '-timedim-presentation').on('change', this.doImageMosaicTimedimPresentationOptionsToggle);
        $('#' + this.name + '-mosaic-granule-format-select').on('change', this.doImageMosaicGranuleLayerSelect);

        $('#' + this.name + '-timedim-format-select').on('change', function() {
             var input = $(this);

             time_re_txt = input.val();

	     var base_name = this.name.split('-timedim')[0];

	     $('#' + base_name + '-timedim-value-valid').show();
        });

        $('#' + this.name + '-timedim-presentation-format-select').on('change', function() {
             var input = $(this);

             var base_name = this.name.split('-timedim')[0];

             if (input.val() === 'DISCRETE_INTERVAL') {
                $('#' + base_name + '-mosaic-timedim-presentation-res-options').show();
             } else {
                $('#' + base_name + '-mosaic-timedim-presentation-res-options').hide();
             }
        });

        $('#' + this.name + '-timedim-defaultvalue-format-select').on('change', function() {
             var input = $(this);

              var base_name = this.name.split('-timedim')[0];

             if (input.val() === 'NEAREST' || input.val() === 'FIXED') {
                $('#' + base_name + '-mosaic-timedim-defaultvalue-res-options').show();
             } else {
                $('#' + base_name + '-mosaic-timedim-defaultvalue-res-options').hide();
             }
        });

        $('#' + this.name + '-timedim-value').on('input', function() {
           var input = $(this);

           var re = new RegExp(time_re_txt, "g");
           var is_valid = re.test(input.val());
           if(is_valid){
	      $('#' + this.name + '-valid').hide();
	   } else {
	      $('#' + this.name + '-valid').show();
           }
        });

        $('#' + this.name + '-timedim-defaultvalue-ref-value').on('input', function() {
           var input = $(this);

           var re = /(\d{4})-(\d{2})-(\d{2})T(\d{2})\:(\d{2})\:(\d{2})[+-](\d{2})\:(\d{2})/;
           var is_valid = re.test(input.val());
           if(is_valid){
		      $('#' + this.name + '-valid').hide();
		   } else {
		      $('#' + this.name + '-valid').show();
	       }
        });

        $('#' + this.name + '\\:geogig_toggle').on('change', this.doGeoGigToggle);

        // Add values to the geogig store dropdown and hide.
        this.setupGeogigDropdown($('#' + this.name.split('.')[0] + '\\:geogig_store'));
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
            var file_ext = file.name.substr(file.name.lastIndexOf('.') + 1);

            var li = $('<li/>').appendTo(ul),
                p = $('<p/>', {text: file.name}).appendTo(li),
                a  = $('<a/>', {text: ' ' + gettext('Remove')});

            if (file_ext === 'xml') {
                $('#metadata_uploaded_preserve_check').show();
            }
            a.data('layer', self.name);
            a.data('file',  file.name);
            a.attr('class', 'remove-file');
            a.appendTo(p);
            a.on('click', function (event) {
                var target = $(event.target),
                    layer_info,
                    layer_name = target.data('layer'),
                    file_name  = target.data('file');
                self.removeFile(file_name);
                if (self.files.length == 0) {
                    delete layers[self.name];
                }
                if (file_ext === 'xml') {
                    $('#metadata_uploaded_preserve_check').hide();
                }
                self.errors = self.collectErrors();
                self.displayErrors();
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

    LayerInfo.prototype.doImageMosaicToggle = function (event) {
        var target = event.target || event.srcElement;
        var id = target.id;
        var base_name = id.split('-mosaic')[0];
        var mosaic_chkbox = $('#' + id).is(':checked');
        if (mosaic_chkbox) {
            $('#' + base_name + '-mosaic-options').show();
        } else {
            $('#' + base_name + '-mosaic-options').hide();
        }
    };

    LayerInfo.prototype.doImageMosaicTimedimOptionsToggle = function (event) {
        var target = event.target || event.srcElement;
        var id = target.id;
        var base_name = id.split('-timedim')[0];
        var mosaic_chkbox = $('#' + id).is(':checked');
        if (mosaic_chkbox) {
            $('#' + base_name + '-mosaic-timedim-options').show();
        } else {
            $('#' + base_name + '-mosaic-timedim-options').hide();
        }
    };

    LayerInfo.prototype.doImageMosaicTimedimPresentationOptionsToggle = function (event) {
        var target = event.target || event.srcElement;
        var id = target.id;
        var base_name = id.split('-timedim')[0];
        var mosaic_chkbox = $('#' + id).is(':checked');
        if (mosaic_chkbox) {
            $('#' + base_name + '-mosaic-timedim-presentation-options').show();
        } else {
            $('#' + base_name + '-mosaic-timedim-presentation-options').hide();
        }
    };

    LayerInfo.prototype.doImageMosaicGranuleOptionsToggle = function (event) {
        var target = event.target || event.srcElement;
        var id = target.id;
        var base_name = id.split('-mosaic')[0];
        var mosaic_chkbox = $('#' + id).is(':checked');
        if (mosaic_chkbox) {
            $('#' + base_name + '-mosaic-granule-format-options').show();

            var dropdown = $('#' + base_name + '-mosaic-granule-format-select');
            // Clear drop down list
            $(dropdown).empty();
            $("<option />", {
                val: '',
                text: 'Select one Mosaic layer ...',
                selected: 'selected'
            }).appendTo(dropdown);
            // Fill drop down list with new data
            $(json_mosaics).each(function () {
                $("<option />", {
                    val: this.name,
                    text: this.name
                }).appendTo(dropdown);
            });

        } else {
            $('#' + base_name + '-mosaic-granule-format-options').hide();
            $('#' + base_name + '-timedim').prop("checked", false);
            $('#' + base_name + '-timedim').prop("disabled", false);
            $('#' + base_name + '-mosaic-timedim-options').hide();
            $('#' + base_name + '-timedim-presentation').prop("checked", false);
            $('#' + base_name + '-timedim-presentation').prop("disabled", false);
            $('#' + base_name + '-mosaic-timedim-presentation-options').hide();
            $('#' + base_name + '-timedim-format-select').val($('#' + base_name + '-timedim-format-select option:first').val());
            $('#' + base_name + '-timedim-format-select').prop("disabled", false);
        }
    };

    LayerInfo.prototype.doImageMosaicGranuleLayerSelect = function (event) {
        var target = event.target || event.srcElement;
        var id = target.id;
        var val = target.value;
        var base_name = id.split('-mosaic')[0];
        if (val !== '') {
            $(json_mosaics).each(function () {
                if (this.name === val) {
                    if (this.has_time === "True") {
                        $('#' + base_name + '-timedim').prop("checked", true);
                        $('#' + base_name + '-timedim').prop("disabled", true);
                        $('#' + base_name + '-mosaic-timedim-options').show();
                        $('#' + base_name + '-timedim-presentation').prop("checked", false);
                        $('#' + base_name + '-timedim-presentation').prop("disabled", true);
                        $('#' + base_name + '-mosaic-timedim-presentation-options').hide();
                        $('#' + base_name + '-timedim-format-select').val(this.time_regex);
                        $('#' + base_name + '-timedim-format-select').prop("disabled", true);
                    }
                    else {
                        $('#' + base_name + '-timedim').prop("checked", false);
                        $('#' + base_name + '-timedim').prop("disabled", false);
                        $('#' + base_name + '-mosaic-timedim-options').hide();
                        $('#' + base_name + '-timedim-presentation').prop("checked", false);
                        $('#' + base_name + '-timedim-presentation').prop("disabled", false);
                        $('#' + base_name + '-mosaic-timedim-presentation-options').hide();
                        $('#' + base_name + '-timedim-format-select').val($('#' + base_name + '-timedim-format-select option:first').val());
                        $('#' + base_name + '-timedim-format-select').prop("disabled", false);
                    }
                }
            });
        }
    };

    return LayerInfo;
});

function updateUrl(url, key, value){
    if (key == null || value == null){
    	return url;
    }

    var pair = key.concat('=').concat(value);

    return (url.lastIndexOf('?') > -1)? url.concat('&').concat(pair): url.concat('?').concat(pair);
}

function format(str, arr) {
  return str.replace(/%(\d+)/g, function(_,m) {
    return arr[--m];
  });
}
