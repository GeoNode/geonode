/*jslint nomen: true */
/*global $:true, document:true, define: true, alert:true, requirejs: true  */

'use strict';

var layers = {};

var geogig_stores = {};

var files_changed = false;

define(['underscore',
        'upload/LayerInfo',
        'upload/FileTypes',
        'upload/path',
        'upload/common',
        'text!templates/upload.html'], function (_, LayerInfo, fileTypes, path, common, uploadTemplate) {

    var templates = {},
        findFileType,
        initialize,
        log_error,
        info,
        types,
        buildFileInfo,
        displayFiles,
        init_geogig_stores,
        doUploads,
        doFormSubmit,
        doSrs,
        doDelete,
        doResume,
        doSuccessfulUpload,
        attach_events,
        checkFiles,
        fileTypes = fileTypes;

    $('body').append(uploadTemplate);

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

        var permission_edit = $("#permission-edit")

        permission_edit.show();
        var hasFullPermissionsWidget = false;

        $.each(layers, function (name, info) {
            if (!info.type) {
                log_error({
                    title: 'Unsupported type',
                    message: interpolate(gettext('The file %s is an unsupported file type, please select another file.',[info.files[0].name]))
                });
                delete layers[name];
            } else {
                info.display(file_queue);
                if(info.type.format=='vector'){
                    hasFullPermissionsWidget = true;
                };
            }
        });

        if(!hasFullPermissionsWidget){permission_edit.hide()};
    };

    /** Function to ...
     *
     *  @params
     *  @returns
     */
    checkFiles = function(){
        var files = layers[Object.keys(layers)[0]]['files'];
        if (!files){
            return false;
        }
        var types = [];
        for (var i = 0; i<files.length; i++){
            var ext = files[i].name.split('.').pop();
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
        var target = event.target || event.srcElement;
        var id = target.id.split("-")[1];
        var target = "/upload/delete/" + id;
        $.ajaxQueue({
            url: target,
            async: false,
            contentType: false,
        }).done(function (resp) {
            var div = "#incomplete-" + id;
            $(div).remove();

            if ($('#incomplete-download-list > div[id^=incomplete]').length == 0){
                $('#incomplete-download-list').hide();
            }

        }).fail(function (resp) {
            //
        });
    };

    doResume = function(event) {
        var target = event.target || event.srcElement;
        var id = target.id.split("-")[1];
        var target = "/upload/?id=" + id;
        $.ajaxQueue({
            url: target,
            async: false,
            contentType: false,
        }).done(function (data) {
          if('redirect_to' in data) {
                common.make_request({
                    url: data.redirect_to,
                    async: false,
                    failure: function (resp, status) {
                        common.logError(resp, status);
                    },
                    success: function (resp, status) {
                        window.location = resp.url;
                    }
                });
            } else if ('url' in data) {
                window.location = data.url;
            } else {
                common.logError("unexpected response");
            }
        }).fail(function (resp) {
            common.logError(resp);
        });
    };

    doSrs = function (event) {
        var form = $("#srsForm")
        $.ajaxQueue({
           type: "POST",
           url: '/upload/srs',
           data: form.serialize(), // serializes the form's elements.
           success: function(data)
           {
               if('redirect_to' in data) {
                    common.make_request({
                        url: data.redirect_to,
                        async: false,
                        failure: function (resp, status) {common.logError(resp); },
                        success: function (resp, status) {
                            window.location = resp.url;
                        }
                    });
                } else if ('url' in data) {
                    window.location = data.url;
                } else {
                    common.logError("unexpected response");
                }
           },
           failure: function (resp, status) {
                common.logError(resp);
           }
        });
        return false;
    };


    /** Function to Upload the selected files to the server
     *
     *  @returns false
     */
    doUploads = function () {
        if ($.isEmptyObject(layers)) {
            doFormSubmit();
            return false;
        }
        var checked = checkFiles();
        if ($.isEmptyObject(layers) || !checked) {
            alert(gettext('You are uploading an incomplete set of files.'));
            console.log('You are uploading an incomplete set of files.');
            $('#please-wait').modal('hide');//to hide please wait modal
        } else {
            $.each(layers, function (name, layerinfo) {
                layerinfo.uploadFiles();
            });
        }
        return false;
    };

    /**Function which submits the form if no

    /** Function which submits the form fields
     *
     */
    doFormSubmit = function(){
        var form = new FormData($("#file-uploader")[0]);
        $.ajax({
           type: "POST",
           url: '/requests/register/data_request/',
           data: form, //form.serialize(), // serializes the form's elements.
           contentType: false,
           processData: false,
           success: function(data)
           {
               if('redirect_to' in data) {
                    common.make_request({
                        url: data.redirect_to,
                        async: false,
                        failure: function (resp, status) {common.logError(resp); },
                        success: function (resp, status) {
                            window.location = resp.url;
                        }
                    });
                } else if ('url' in data) {
                    window.location = data.url;
                } else {
                    common.logError("unexpected response");
                }
            },
            error: function(data){
                var errors = $.parseJSON(data.responseText).errors;
                $('#please-wait').modal('hide');
                for (var key in errors ){
                    $('#div_id_'+key).addClass('has-error');
                    $('#div_id_'+key).find('div').append("<span id=\"error_id_"+key+"\" class=\"error-msg\">"+errors[key]+"</span>");
                }
            }
        });

     }



    /** Function to ...
     *
     *  @returns false
     */
    init_geogig_stores = function() {
        $.ajax({
            url: '/gs/rest/stores/geogig/',
            async: true,
            contentType: false,
        }).done(function (resp) {
            geogig_stores = JSON.parse(resp);
        }).fail(function (resp) {
            //
        });
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
                // http://stackoverflow.com/questions/1043957/clearing-input-type-file-using-jquery/13351234#13351234
                $("#file-input").wrap('<form>').closest('form').get(0).reset();
                $("#file-input").unwrap();
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
            if (files_changed){
                buildFileInfo(_.groupBy(file_input.files, path.getName));
                displayFiles(file_queue);
                files_changed = false;
          }
        });

        $("#file-input").change(function (event) {
            files_changed = true;
        });


        $(options.clear_button).on('click', doClearState);
        $(options.upload_button).on('click', doUploads);
        $("[id^=delete]").on('click', doDelete);
        $("[id^=resume]").on('click', doResume);
        if (geogig_enabled) {
            init_geogig_stores();
        }
    };

    // public api

    return {
        initialize: initialize,
        doSrs: doSrs,
        doDelete: doDelete,
        doResume: doResume
    };

});
