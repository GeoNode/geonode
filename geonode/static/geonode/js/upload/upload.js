/*global $:true, document:true, define: true, alert:true, requirejs: true  */

'use strict';

define(['jquery',
        'underscore',
        'upload/LayerInfo',
        'upload/FileTypes',
        'text!templates/upload.html'], function ($, _, LayerInfo, fileTypes, upload) {

    var layers = {},
        templates = {},
        findFileType,
        initialize,
        log_error,
        info,
        types,
        buildFileInfo,
        displayFiles,
        doUploads,
        doSuccessfulUpload,
        attach_events;

    $('body').append(upload);

    templates.errorTemplate = _.template($('#errorTemplate').html());

    templates.infoTemplate = _.template($('#infoTemplate').html());

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

    doUploads = function () {
        if ($.isEmptyObject(layers)) {
            alert('You must select some files first.');
        } else {
            $.each(layers, function (name, layerinfo) {
                layerinfo.uploadFiles();
            });
        }
    };

    initialize = function (options) {
        var file_input = document.getElementById('file-input'),
            file_queue = $(options.file_queue);

        $(options.form).change(function (event) {
            // this is a mess
            buildFileInfo(_.groupBy(file_input.files, LayerInfo.getName));
            displayFiles(file_queue);
        });

        $(options.upload_button).on('click', doUploads);
    };

    // public api

    return {
        initialize: initialize
    };

});
