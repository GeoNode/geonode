/*jslint nomen: true */
/*global $:true, document:true, define: true, alert:true, requirejs: true  */

'use strict';

var layers = {};

define(['jquery',
        'underscore',
        'upload/LayerInfo',
        'upload/FileTypes',
        'upload/path',
        'upload/common',
        'text!templates/upload.html'], function ($, _, LayerInfo, fileTypes, path, common, upload) {

    var templates = {},
        findFileType,
        initialize,
        log_error,
        info,
        types,
        buildFileInfo,
        displayFiles,
        doUploads,
        doTime,
        doSrs,
        doDelete,
        doResume,
        doSuccessfulUpload,
        attach_events,
        checkFiles,
        fileTypes = require('upload/FileTypes');

    $('body').append(upload);

    templates.errorTemplate = _.template($('#errorTemplate').html());

    templates.infoTemplate = _.template($('#infoTemplate').html());

    /** Function to log errors to the #global-errors div 
     *
     *  @params {options}
     *  @returns {string}
     */
    log_error = function (options) {
        $('#global-errors').append(templates.errorTemplate(options));
    };

    /** Info function takes an object and returns a correctly
     *  formatted bootstrap alert element.
     *
     *  @returns {string}
     */
    info = function (options) {
        return templates.infoTemplate(options);
    };


    /* Function to iterates through all of the known types and returns the
     * type if it matches, if not return null
     * @params {File}
     * @returns {object}
     */
    findFileType = function (file) {
        var i, type;
        for (i = 0; i < types.length; i += 1) {
            type = types[i];
            if (type.isType(file)) {
                return {type: type, file: file};
            }
        }
    };


    /** Function to ...
     *
     *  @params  
     *  @returns
     */
    buildFileInfo = function (files) {
        var name, info;

        for (name in files) {
            // filter out the prototype properties

            if (files.hasOwnProperty(name)) {

                // check to see if the layer was already defined

                if (layers.hasOwnProperty(name)) {
                    info = layers[name];
                    $.merge(info.files, files[name]);
                    info.displayFiles();
                } else {
                    info = new LayerInfo({
                        name: name,
                        files: files[name]
                    });
                    info.collectErrors();
                    layers[name] = info;
                }
            }
        }
    };


    /** Function to ...
     *
     *  @params  
     *  @returns
     */
    displayFiles = function (file_queue) {
        file_queue.empty();

        $.each(layers, function (name, info) {
            if (!info.type) {
                log_error({
                    title: 'Unsupported type',
                    message: 'File ' + info.name + ' is an unsupported file type, please select another file.'
                });
                delete layers[name];
            } else {
                info.display(file_queue);
            }
        });
    };


    /** Function to ...
     *
     *  @params  
     *  @returns
     */
    checkFiles = function(){
        var files = layers[Object.keys(layers)[0]]['files'];
        var types = [];
        for (var i = 0; i<files.length; i++){
            var ext = files[i].name.split('.')[1];
            if ($.inArray(ext,types) == -1){
                types.push(ext);
            }
        }
        var matched = false;
        for (var file_type in fileTypes){
            var required = fileTypes[file_type]['requires'];
            if ($(required).not(types).length == 0){
                matched = true;
                break;
            }
            else{
                matched = false;
            }
        }
        return matched;
    }

    doDelete = function(event) {
        var id = event.srcElement.id.split("-")[1];
        var target = "/upload/delete/" + id;
        $.ajax({
            url: target,
            async: false,
            contentType: false,
        }).done(function (resp) {
            var div = "incomplete-" + id;
            $(div).hide();
        }).fail(function (resp) {
            //
        });
    };

    doResume = function(event) {
        var id = event.srcElement.id.split("-")[1];
        var target = "/upload/?id=" + id;
        $.ajax({
            url: target,
            async: false,
            contentType: false,
        }).done(function (data) {
          if('redirect_to' in data) {
                common.make_request({
                    url: data.redirect_to,
                    async: false,
                    failure: function (resp, status) {
                        self.markError(resp, status); 
                    },
                    success: function (resp, status) {
                        window.location = resp.url;
                    },
                });
            } else if ('url' in data) {
                window.location = data.url;
            } else {
                self.markError(resp, status); 
            }
        }).fail(function (resp) {
            self.markError(resp, status); 
        });
    };

    doSrs = function (event) {
        var form = $("#srsForm")
        $.ajax({
           type: "POST",
           url: '/upload/srs',
           data: form.serialize(), // serializes the form's elements.
           success: function(data)
           {
               if('redirect_to' in data) {
                    common.make_request({
                        url: data.redirect_to,
                        async: false,
                        failure: function (resp, status) {self.markError(resp, status); },
                        success: function (resp, status) {
                            window.location = resp.url;
                        },
                    });
                } else if ('url' in data) {
                    window.location = data.url; 
                } else {
                    self.markError(resp, status); 
                }
           },
           failure: function (resp, status) {
                self.markError(resp, status); 
           },
        });
        return false; 
    };

    doTime = function (event) {
        var form = $("#timeForm")
        $.ajax({
           type: "POST",
           url: '/upload/time',
           data: form.serialize(), // serializes the form's elements.
           success: function(data)
           {
               if('redirect_to' in data) {
                    common.make_request({
                        url: data.redirect_to,
                        async: false,
                        failure: function (resp, status) {self.markError(resp, status); },
                        success: function (resp, status) {
                            window.location = resp.url;
                        },
                    });
                } else if ('url' in data) {
                    window.location = data.url; 
                } else {
                    self.markError(resp, status); 
                }
           },
           failure: function (resp, status) {
                    self.markError(resp, status); 
           },
        });
        return false;        
    };

    /** Function to ...
     *
     *  @params  
     *  @returns
     */
    doUploads = function () {
        var checked = checkFiles();
        if ($.isEmptyObject(layers) || !checked) {
            alert('You are uploading an incomplete set of files.');
        } else {
            $.each(layers, function (name, layerinfo) {
                layerinfo.uploadFiles();
            });
        }
    };


    /** Initialization function. Called from main.js 
     *
     *  @params  
     *  @returns
     */
    initialize = function (options) {
        var file_input = document.getElementById('file-input'),
            dropZone = document.querySelector(options.dropZone),
            file_queue = $(options.file_queue),
            doClearState = function () {
                // set the global layer object to empty
                layers = {};
                // redraw the file display view
                displayFiles(file_queue);
            },
            runUpload = function (files) {
                buildFileInfo(_.groupBy(files, path.getName));
                displayFiles(file_queue);
            },
            handleDragOver = function (e) {
                // this seems to be required in order for dragging and dropping to work
                e.stopPropagation();
                e.preventDefault();
                e.dataTransfer.dropEffect = 'copy';
                return false;
            };

        // setup the drop zone target
        dropZone.addEventListener('dragover', handleDragOver, false);

        dropZone.addEventListener('drop', function (e) {
            e.preventDefault();
            var files = e.dataTransfer.files;
            runUpload(files);
        });

        $(options.form).change(function (event) {
            // this is a mess
            buildFileInfo(_.groupBy(file_input.files, path.getName));
            displayFiles(file_queue);
        });
        $(options.clear_button).on('click', doClearState);
        $(options.upload_button).on('click', doUploads);
        $("[id^=delete]").on('click', doDelete);
        $("[id^=resume]").on('click', doResume);
    };

    // public api

    return {
        initialize: initialize,
        doTime: doTime,
        doSrs: doSrs,
        doDelete: doDelete,
        doResume: doResume
    };

});
