/*jslint nomen: true */
/*global define:true, $:true, FormData: true, alert: true, window:true */
'use strict';

define(function (require, exports) {
        var _      = require('underscore'),
        fileTypes  = require('./FileTypes'),
        path       = require('./path'),
        common     = require('./common'),
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
        var extensions = this.getExtensions();
        $.each(fileTypes, function (name, type) {
            if (type.isType(file, extensions)) {
                res = {type: type, file: file};
                // return false;
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

            // if we find the type of the file, we also find the "main" file
            if (results) {
                if (results.type.main == 'kml') {
                   // Assume the kml file always as main one
                   self.type = results.type;
                   self.main = results.file;
                } else if ((results.type.main == 'xml' || results.type.main == 'sld') &&
                        self.main != undefined) {
                   // Do not assume the metadata or sld file as main one
                   self.type = self.type;
                   self.main = self.main;
               } else if ((self.type == undefined) || (self.type != undefined && self.type.main != 'kml')) {
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
        var i, ext, file, perm, time, mosaic;

        var base_ext  = this.main.name.split('.').pop();
        var base_name = this.name;

        var base_ext  = this.main.name.split('.').pop();
        var base_name = this.name;

        var base_ext  = this.main.name.split('.').pop();
        var base_name = this.name;

        if (!form_data) {
            form_data = new FormData();
        }
        // this should be generated from the permission widget
        if (typeof permissionsString == 'undefined'){
            perm = {}
        }
        else {
            perm = permissionsString('#permission_form','datasets');
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
             form_data.append('dataset_title', $('#id_dataset_title').val());
        }
        if ($('#id_metadata_uploaded_preserve').prop('checked')) {
             form_data.append('metadata_uploaded_preserve', true);
        }
        if ($('#id_style_upload_form').prop('checked')) {
             form_data.append('style_upload_form', true);
             form_data.append('dataset_title', $('#id_dataset_title').val());
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
        var default_message = gettext("Unexpected error!");

        if (status == 400) {
            default_message += gettext(" - 400 Bad Request. Server cannot or will not process the request due to something that is perceived to be a client error (e.g., malformed request syntax, invalid request message framing, or deceptive request routing).");
        }
        else if (status == 401) {
            default_message += gettext(" - 401 Unauthorized. Request was not sent with the proper authentication credentials.");
        }
        else if (status == 403) {
            default_message += gettext(" - 403 Forbidden. This is generally related to permission rules on your server. Contact the system administrator for more information regarding this error message.");
        }
        else if (status == 404) {
            default_message += gettext(" - 404 Not Found. Origin server was unable or unwilling to find the resource requested.");
        }
        else if (status == 405) {
            default_message += gettext(" - 405 Method Not Allowed. Origin server is aware of the requested resource, but the request method used is not supported.");
        }
        else if (status == 406) {
            default_message += gettext(" - 406 Not Acceptable. Resource is not available at the origin that adheres to negotiation headers that were  set prior (e.g. via 'Accept-Charset' and 'Accept-Language' headers).");
        }
        else if (status == 407) {
            default_message += gettext(" - 407 Authentication Required. The client did not send the required authentication with the request.");
        }
        else if (status == 408) {
            default_message += gettext(" - 408 Request Timeout. The origin server did not receive the complete request in what it considers a reasonable time.");
        }
        else if (status == 409) {
            default_message += gettext(" - 409 Conflict. The request did not complete because of a conflict with the current state of the resource. Typically happens on a PUT request where multiple clients are attempting to edit the same resource.");
        }
        else if (status == 410) {
            default_message += gettext(" - 410 Gone. The resource requested is permanently missing at the origin.");
        }
        else if (status == 411) {
            default_message += gettext(" - 411 Length Required. Client did not define the 'Content-Length' of the request body in the headers and this is required to obtain the resource.");
        }
        else if (status == 412) {
            default_message += gettext(" - 412 Precondition Failed. Server denies the request because the resource failed to meet the conditions specified by the client.");
        }
        else if (status == 413) {
            default_message += gettext(" - 413 Payload Too Large. Refusal from the server to process the request because the payload sent from the client is larger than the server wished to accept. Server has the optional to close the connection.");
        }
        else if (status == 414) {
            default_message += gettext(" - 414 URI Too Long. Refusal from the server that the URI was too long to be processed. For example, if a client is attempting a GET request with an unusually long URI after a POST, this could be seen as a security risk and a 414 gets generated.");
        }
        else if (status == 415) {
            default_message += gettext(" - 415 Unsupported Media Type. Refusal from the server to process the format of the current payload. One way to identify and fix this issue would be to look at the 'Content-Type' or 'Content-Encoding' headers sent in the client’s request.");
        }
        else if (status == 417) {
            default_message += gettext(" - 417 Expectation Failed. Failure of server to meet the requirements specified in the 'Expect' header of the client’s request.");
        }
        else if (status == 429) {
            default_message += gettext(" - 429 Too Many Requests. Client has sent too many requests in the specified amount of time according to the server.");
        }
        else if (status == 499) {
            default_message += gettext(" - 499 Client Close Request. Nginx specific response code to indicate when the connection has been closed by the client while the server is still processing its request, making server unable to send a status code back.");
        }
        else if (status == 500) {
            default_message += gettext(" - 500 Internal Server Error. This error indicates that the server has encountered an unexpected condition. This often occurs when an application request cannot be fulfilled due to the application being configured incorrectly on the server.");
        }
        else if (status == 501) {
            default_message += gettext(" - 501 Not Implemented. This error indicates that the HTTP method sent by the client is not supported by the server. This is most often caused by the server being out of date. It is a very rare error and generally requires that the web server be updated.");
        }
        else if (status == 502) {
            default_message += gettext(" - 502 Bad Gateway. This error is usually due to improperly configured proxy servers. The first step in resolving the issue is to clear the client's cache.");
        }
        else if (status == 503) {
            default_message += gettext(" - 503 Service Unavailable. This error occurs when the server is unable to handle requests due to a temporary overload or due to the server being temporarily closed for maintenance. The error indicates that the server will only temporarily be down.");
        }
        else if (status == 504) {
            default_message += gettext(" - 504 Gateway Timeout. GeoNode lost the connection with GeoServer or DB due to a connection timeout. Consider using the management commands to import data!");
        }
        else if (status == 505) {
            default_message += gettext(" - 505 HTTP Version Not Supported. This error occurs when the server refuses to support the HTTP protocol that has been specified by the client computer. This can be caused by the protocol not being specified properly by the client computer; for example, if an invalid version number has been specified.");
        }
        else if (status == 506) {
            default_message += gettext(" - 506 Variant Also Negotiates. This error indicates that the server is not properly configured. Contact the system administrator to resolve this issue.");
        }
        else if (status == 507) {
            default_message += gettext(" - 507 Insufficient Storage. This error indicates that the server is out of free memory. This is most likely to occur when an application that is being requested cannot allocate the necessary system resources to run. To resolve the issue, the server's hard disk may need to be cleaned of any unnecessary documents to free up more hard disk space, its memory may need to be expanded, or it may simply need to be restarted. Contact the system administrator for more information regarding this error message.");
        }
        else if (status == 509) {
            default_message += gettext(" - 509 Bandwidth Limit Exceeded. This error occurs when the bandwidth limit imposed by the system administrator has been reached. The only fix for this issue is to wait until the limit is reset in the following cycle. Consult the system administrator for information about acquiring more bandwidth.");
        }
        else if (status == 510) {
            default_message += gettext(" - 510 Not Extended. This error occurs when an extension attached to the HTTP request is not supported by the web server. To resolve the issue, you may need to update the server.");
        }
        else {
            default_message += " - " + gettext("Unknwon") + gettext(" Error Code. Contact the system administrator for more information regarding this error message.");
        }
        if (error != undefined) {
            default_message += " " + gettext("Additional info: ") + "[" + error + "]";
        }
        common.logError(default_message, this.element.find('#status'));
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

    LayerInfo.prototype.markEnd = function () {
        this.logStatus({
            msg: 'Your upload was succesfull!',
            level: 'alert-success',
            empty: 'true'
        });
    };

    LayerInfo.prototype.doResume = function (event) {
        $(this).text(gettext('Finalizing')).attr('disabled', 'disabled').after('<img class="pull-right" src="../../static/geonode/img/loading.gif">');
        var id = (new Date()).getTime();
        /* ****
         * AF: Switching those two below allows to open a new window instead of redirecting
         *     the active one.
         * ****/
	    // var newWin = window.open(window.location.href,
        //        id, "toolbar=1,scrollbars=1,location=0,statusbar=0,menubar=1,resizable=1,width=1100,height=800,left = 240,top = 100");
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
                    /* ****
                     * AF: Switching those two below allows to open a new window instead of redirecting
                     *     the active one.
                     * ****/
                    window.location = resp.url;
                    /* newWin.location = resp.url;
                    newWin.focus(); */
                }else {
                    /* ****
                     * AF: Switching those two below allows to open a new window instead of redirecting
                     *     the active one.
                     * ****/
                    window.location = resp.redirect_to;
                    /* newWin.location = resp.redirect_to;
                    newWin.focus(); */
                }
            },
        });
        return false;
    };

    String.prototype.capitalize = function() {
        return this.charAt(0).toUpperCase() + this.slice(1);
    };

    LayerInfo.prototype.displayUploadedLayerLinks = function(resp) {
        var self = this;
        var resourceType = 'dataset';
        try {
            resourceType = /^\/(.*)s\/.*/.exec(resp.url)[1];
        } catch (err) {
            // pass
        }
        var info_message = gettext('Your ' + resourceType +' was successfully created.');
        var a = '<a href="' + resp.url + '" class="btn btn-success">' + gettext(resourceType.capitalize() + ' Info') + '</a>&nbsp;&nbsp;&nbsp;';
        if(resourceType == 'dataset') {
            // Only Layers have Metadata and SLD Upload features for the moment
            info_message += ' ' + gettext('Please wait until GeoNode finished configuring it!');
            a = '';
        }
        var msg_col = "";
        if (resp.info){
            var msg_template = gettext('The column %1 was renamed to %2 <br/>');
            for (var key in resp.info){
               msg_col += format(msg_template,[key,resp.info[key]]);
            }
        }
        self.logStatus({
            msg: '<p>' + info_message + '<br/>' + msg_col + '<br/>' + a + '</p>',
            level: 'alert-success',
            empty: 'true'
        });
    };

    LayerInfo.prototype.startPolling = function(execution_id) {
        var self = this;
        const baseUrl = executions_status_endpoint;
        if (self.polling) {
            $.ajax({ 
                url: baseUrl + "?import&filter{source}=resource_file_upload&page=1&page_size=99999", type: 'GET', success: function(data){
                // TODO: Not sure we need to do anything here?
                //console.log('polling');
                }, 
                dataType: "json", 
                success: function(resp, code) {
                    if (resp.requests && resp.requests.length>0) {
                        const execution_data = resp.requests.find((req) => req.exec_id === execution_id);
                        if (execution_data.status == 'finished'){
                            self.polling = false;
                            self.markEnd();
                            $.ajax({url: baseUrl + "/" + execution_id, type: "DELETE"});
                            if (execution_data.output_params && execution_data.output_params['detail_url']) {
                                const detail_url = execution_data.output_params['detail_url'];
                                if (detail_url != '') {
                                    window.location = detail_url;
                                }
                            }
                            
                        }
                    }
                    setTimeout(function() {self.startPolling(execution_id)}, 3000)
                },
                timeout: 30000
            })
        }
    };

    /** Function to deal with the final step in the upload process
     *
     *  @params {options}
     *  @returns {string}
     */
    LayerInfo.prototype.doFinal = function (resp, callback, array) {
        var self = this;
        if (resp.hasOwnProperty('redirect_to') && resp.redirect_to.indexOf('upload/final') > -1) {
            common.make_request({
                url: '#',
                async: true,
                beforeSend: function() {
                    self.logStatus({
                        msg: '<p>' + gettext('Performing Final GeoServer Config Step. Check the Upload status above!') + '</p>',
                        level: 'alert-success',
                        empty: 'true'
                    });
                    self.polling = true;
                    self.startPolling();
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
                            self.doFinal(resp, callback, array);
                        }, 5000);
                    } else if (resp.status === 'error') {
                        self.polling = false;
                        self.markError(resp.error_msg, resp.status);
                        callback(array);
                    } else {
                        // self.displayUploadedLayerLinks(resp);
                        callback(array);
                    }
                }
            });
        } else if (resp.status === "incomplete") {
            var id = common.parseQueryString(resp.url).id;
            var element = 'next_step_' + id
            var a = '<a id="' + element + '" class="btn btn-primary" target="_blank">Continue</a>';
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

            callback(array);

            return;
        } else if (resp.status === "other") {
            self.logStatus({
                msg:'<p>' + gettext('You need to specify more information in order to complete your upload') + '</p>',
                level: 'alert-success',
                empty: 'true'
            });

            callback(array);
        } else if (resp.status === 'error') {
            self.polling = false;
            self.markError(resp.error_msg, resp.status);

            callback(array);
        } else if (resp.success === true) {
            self.polling = false;
            self.displayUploadedLayerLinks(resp);

            callback(array);
        } else {
            self.polling = false;
            resp.errors = 'Unexpected Error';
            self.logStatus({
                msg:'<p>' + gettext('Unexpected Error') + '</p>',
                level: 'alert-error',
                empty: 'true'
            });

            callback(array);
        }

    };

    /** Function to deal with the Steps in the upload process
     *
     *  @params {options}
     *  @returns {string}
     */
    LayerInfo.prototype.doStep = function (resp, callback, array) {
        var self = this;
        self.logStatus({
            msg: '<p>' + gettext('Performing GeoServer Config Step') + '<img class="pull-right" src="../../static/geonode/img/loading.gif"></p>',
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

                    callback(array);
                },
                success: function (resp, status) {
                    self.id = resp.id;
                    if (resp.status === 'incomplete') {
                        if (resp.input_required === true) {
                            self.doFinal(resp, callback, array);
                        } else {
                            setTimeout(() => {
                                self.doStep(resp, callback, array);
                            }, 1000);
                        }
                    } else if (resp.status === 'error') {
                        self.polling = false;
                        self.markError(resp.error_msg, resp.status);
                        callback(array);
                    } else if (resp.redirect_to.indexOf('upload/final') > -1) {
                        self.doFinal(resp, callback, array);
                    } else {
                        window.location = resp.url;
                    }
                }
            });
        } else if (resp.success === true && resp.status === 'error') {
            self.polling = false;
            self.markError(resp.error_msg, resp.status);
            callback(array);
        } else if (resp.success === true && typeof resp.url != 'undefined') {
            self.doFinal(resp, callback, array);
        } else if (resp.success === true && resp.redirect_to.indexOf('upload/final') > -1) {
            self.doFinal(resp, callback, array);
        }
    };

    /** Function to upload the files against the specified endpoint
     *
     *  @params
     *  @returns
     */
     LayerInfo.prototype.uploadFiles = function (callback, array) {
        var form_data = this.prepareFormData(), self = this;
        var prog = "";

        $.ajax({
            url: form_target,
            async: true,
            mode: "queue",
            type: "POST",
            data: form_data,
            timeout: 600000, // sets timeout to 10 minutes
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
            },
            error: function (jqXHR) {
                self.polling = false;
                if (jqXHR.status === 500 || jqXHR.status === 0 || jqXHR.readyState === 0) {
                  var error = 'Server Error: ' + jqXHR.statusText + gettext('<br>Please check your network connection. In case of Layer Upload make sure GeoServer is running and accepting connections.');
                  if (jqXHR.responseJSON !== undefined && jqXHR.responseJSON !== null) {
                      if (jqXHR.responseJSON.errors !== undefined || jqXHR.responseJSON.error_msg !== undefined) {
                          error = jqXHR.responseJSON.errors !== undefined ? jqXHR.responseJSON.errors : jqXHR.responseJSON.error_msg;
                      }
                  }
                  self.markError(error);
                } else if (jqXHR.status === 400 || jqXHR.status === 404) {
                  if (jqXHR.responseJSON !== undefined && jqXHR.responseJSON !== null) {
                      if (jqXHR.responseJSON.errors !== undefined) {
                          self.markError('Client Error: ' + jqXHR.statusText + gettext('<br>' + jqXHR.responseJSON.errors));
                      }
                  } else if (jqXHR.responseText !== undefined && jqXHR.responseText !== null) {
                      self.markError('Client Error: ' + jqXHR.statusText + gettext('<br>' + jqXHR.responseText));
                  } else {
                      self.markError('Client Error: ' + jqXHR.statusText + gettext('<br>Bad request or URL not found.'));
                  }
                } else {
                  if (jqXHR.responseJSON !== undefined && jqXHR.responseJSON !== null) {
                      if (jqXHR.responseJSON.errors !== undefined) {
                          self.markError('Unexpected Error: ' + jqXHR.statusText + gettext('<br>' + jqXHR.responseJSON.errors));
                      }
                  } else if (jqXHR.responseText !== undefined && jqXHR.responseText !== null) {
                      self.markError('Unexpected Error: ' + jqXHR.statusText + gettext('<br>' + jqXHR.responseText));
                  } else {
                      self.markError('Unexpected Error: ' + jqXHR.statusText + gettext('<br>Unknown.'));
                  }
                }

                callback(array);
            },
            success: function (resp, status) {
                /*self.logStatus({
                    msg: '<p>' + gettext('Layer files uploaded, configuring in GeoServer') + '</p>',
                    level: 'alert-success',
                    empty: 'true'
                });
                self.id = resp.id;
                self.doStep(resp, callback, array);
                */
                self.polling = true;
                self.startPolling(resp.execution_id);
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

        var layerTemplate = _.template($('#layerTemplate').html()),
            li = layerTemplate({
                name: this.name,
                selector: LayerInfo.safeSelector(this.name),
                type: this.type.name,
                format: this.type.format,
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
            layer_name = target.data('dataset'),
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
            a.data('dataset', self.name);
            a.data('file',  file.name);
            a.attr('class', 'remove-file');
            a.appendTo(p);
            a.on('click', function (event) {
                var target = $(event.target),
                    layer_info,
                    layer_name = target.data('dataset'),
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
                text: 'Select one Mosaic dataset ...',
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
