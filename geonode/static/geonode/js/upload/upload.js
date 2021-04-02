/*jslint nomen: true */
/*global $:true, document:true, define: true, alert:true, requirejs: true  */

'use strict';

var layers = {};

define(['underscore',
        './LayerInfo',
        './FileTypes',
        './path',
        './common',
        'text!templates/upload.html'], function (_, LayerInfo, fileTypes, path, common, uploadTemplate) {

    var templates = {},
        findFileType,
        initialize,
        log_error,
        info,
        types,
        buildFileInfo,
        displayFiles,
        doUpload,
        doUploads,
        doSrs,
        doUpdateIncompleteUploads,
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
                    // if (Object.keys(layers).length == 0) {
                        info = new LayerInfo({
                            name: name,
                            files: files[name]
                        });
                        info.collectErrors();
                        layers[name] = info;
                    /* } else {
                        log_error({
                            title: 'Wrong selection',
                            message: gettext('Only one File at a time can be uploaded!')
                        });
                    } */
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
                    message: interpolate(gettext('The file %s is an unsupported file type, please select another file.'),[info.files[0].name])
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
        var types = [];
        for (var i = 0; i<files.length; i++){
            var base_name = files[i].name.split('.')[0].replace(/\[|\]|\(|\)| /g, '_');
            var ext = files[i].name.split('.').pop().toLowerCase();
            if ($.inArray(ext,types) == -1){
                types.push(ext);
            }

            var mosaic_is_valid = true;
            var is_granule = $('#' + base_name + '-mosaic').is(':checked');

            var is_time_enabled = $('#' + base_name + '-timedim').is(':checked');
            var is_time_valid = is_time_enabled && !$('#' + base_name + '-timedim-value-valid').is(':visible');

            if (is_granule && is_time_enabled) {
                mosaic_is_valid = is_time_valid;
            }

            var is_adv_options_enabled = $('#' + base_name + '-timedim-presentation').is(':checked');
            var default_value = $('#' + base_name + '-timedim-defaultvalue-format-select').val();

            if (default_value == 'NEAREST' || default_value == 'FIXED') {
                var is_reference_value_valid = is_adv_options_enabled && !$('#' + base_name + '-timedim-defaultvalue-ref-value-valid').is(':visible')
                mosaic_is_valid = is_time_valid && is_reference_value_valid;
            }

            if (is_granule && !mosaic_is_valid) {
                return false;
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

    doSrs = function (event) {
        var form = $("#srsForm")
        $.ajax({
           type: "POST",
           mode: "queue",
           url: siteUrl + 'upload/srs',
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
     */
    doUpload = function (layers) {
        if (layers.length > 0) {
            layers[0].uploadFiles(doUpload, layers.slice(1, layers.length));
        }
    };

    /** Function to Upload the selected files to the server
     *
     *  @returns false
     */
    doUploads = function () {
        if ($.isEmptyObject(layers)) {
            common.logError('Please provide some files');
            return false;
        }

        var checked = checkFiles();
        if ($.isEmptyObject(layers) || !checked) {
            alert(gettext('You are trying to upload an incomplete set of files or not all mandatory options have been validated.\n\nPlease check for errors in the form!'));
        } else {
            /* $.each(layers, function (name, layerinfo) {
                layerinfo.uploadFiles();
            }); */

            var layerInfos = [];
            $.each(layers, function (name, layerinfo) {
                layerInfos.push(layerinfo);
            });
            doUpload(layerInfos);
        }
        return false;
    };

    doUpdateIncompleteUploads = function() {

        const row = $( this ).get(0);
        const intervalTime = 5000; // 5 seconds
        const id = row.getAttribute('data-upload-id') || '';
        const target = siteUrl + 'api/v2/uploads/' + id;
        const progressNode = row.querySelector('.incomplete-progress');

        var incompleteProgressInterval;
        var resumeUrl = '';
        var deleteUrl = '';

        function handleDelete() {
            $.ajax({
                url: deleteUrl,
                async: false,
                mode: 'queue',
                contentType: false,
            })
                .done(function () {
                    // if the upload is successfully removed
                    // - remove the node
                    // - hide the incomplete download list if there are not child
                    $('#incomplete-' + id).remove();
                    if ($('#incomplete-download-list [data-upload-id]').length == 0){
                        $('#incomplete-download-list').hide();
                    }
                    // if removed stop request on this node
                    if (incompleteProgressInterval) {
                        clearInterval(incompleteProgressInterval);
                    }
                })
                .fail(function () {
                    //
                });
        }

        function handleResume() {
            $.ajax({
                url: resumeUrl,
                async: false,
                mode: "queue",
                contentType: false,
            })
                .done(function (data) {
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
                })
                .fail(function (resp) {
                    common.logError(resp);
                });
        }

        const resumeNode = row.querySelector('.incomplete-resume');
        resumeNode.addEventListener('click', handleResume);
        const removeNode = row.querySelector('.incomplete-remove');
        removeNode.addEventListener('click', handleDelete);
        const linkDetailNode = row.querySelector('.incomplete-link');

        progressNode.style.position = 'relative';
        progressNode.innerHTML = '';

        // add a small progress bar in the progressNode
        const progressBarBg = document.createElement('div');
        progressBarBg.style.position = 'absolute';
        progressBarBg.style.left = 0;
        progressBarBg.style.bottom = 0;
        progressBarBg.style.width = '100%';
        progressBarBg.style.height = '4px';
        progressNode.appendChild(progressBarBg);

        const progressBar = document.createElement('div');
        progressBar.style.position = 'absolute';
        progressBar.style.left = 0;
        progressBar.style.bottom = 0;
        progressBar.style.width = 0;
        progressBar.style.height = '4px';
        progressBar.style.transition = '0.3s width';
        progressNode.appendChild(progressBar);

        // write the current progress percentage in the progressNode
        const progressLabel = document.createElement('span');
        progressNode.appendChild(progressLabel);

        function requestStateProgress(resolve, reject) {
            $.ajax({
                url: target,
                async: false,
                mode: "queue",
                contentType: false,
            })
                .done(function (response) {
                    const uploadProperties = response && response.upload || {};
                    resolve(uploadProperties);
                })
                .fail(function (error) { reject(error); });
        }

        // change style of rows in the incomplete upload list based on the state
        function updateRowStructure(uploadProperties) {
            progressBarBg.style.backgroundColor = '#f2f2f2';
            progressBar.style.backgroundColor = '#27ca3b';
            resumeNode.style.display = 'none';
            removeNode.style.display = 'none';
            linkDetailNode.style.display = 'none';
            resumeUrl = uploadProperties.resume_url;
            deleteUrl = uploadProperties.delete_url;
            row.setAttribute('class', '');
            switch(uploadProperties.state) {
                case 'PENDING':
                    resumeNode.style.display = 'inline-block';
                    removeNode.style.display = 'inline-block';
                    progressBarBg.style.backgroundColor = '#ccc';
                    progressBar.style.backgroundColor = '#999';
                    row.setAttribute('class', 'active');
                    break;
                case 'PROCESSED':
                    linkDetailNode.style.display = 'inline-block';
                    row.setAttribute('class', 'success');
                    break;
                case 'INVALID':
                    removeNode.style.display = 'inline-block';
                    row.setAttribute('class', 'danger');
                    break;
                default:
                    removeNode.style.display = 'inline-block';
                    break;
            }
        }

        requestStateProgress(function(initialUploadProperties) {
            // set initial value for the progress bar
            const initialProgress = Math.round(initialUploadProperties.progress)  + '%';
            progressLabel.innerHTML = initialProgress;
            progressBar.style.width = initialProgress;

            updateRowStructure(initialUploadProperties);

            if (initialProgress !== '100%') {
                incompleteProgressInterval = setInterval(function() {
                    // check if the progressNode is still in the page
                    // and stop the request for an update
                    if (document.body.contains(progressNode)) {
                        requestStateProgress(function(uploadProperties) {
                            // set updated value for the progress bar
                            updateRowStructure(uploadProperties);
                            const progress = Math.round(uploadProperties.progress)  + '%';
                            progressLabel.innerHTML = progress;
                            progressBar.style.width = progress;

                            // stop the requests once the progress is 100%
                            if (progress === '100%') {
                                // add visibility the link to detail if available
                                const detailUrl = uploadProperties.layer && uploadProperties.layer.detail_url;
                                linkDetailNode.style.display = 'none';
                                resumeNode.style.display = 'none';
                                removeNode.style.display = 'none';
                                if (detailUrl) {
                                    linkDetailNode.style.display = 'inline-block';
                                    linkDetailNode.setAttribute('href', detailUrl);
                                }
                                clearInterval(incompleteProgressInterval);
                            }
                        }, function(error) {
                            //
                        });
                    } else {
                        clearInterval(incompleteProgressInterval);
                    }
                }, intervalTime);
            }
        }, function(error) {
            //
        });
    }

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
            buildFileInfo(_.groupBy(file_input.files, path.getName));
            displayFiles(file_queue);
            // Reset the file upload form so the user can reupload the same file
            $('#file-uploader').get(0).reset();
        });
        // Detect click on "Remove" link and update the file_queue
        $(options.file_queue).on('click', '.remove-file', function () {
            displayFiles(file_queue);
        });
        $(options.clear_button).on('click', doClearState);
        $(options.upload_button).on('click', doUploads);
        $('[data-upload-id]').each(doUpdateIncompleteUploads);
        $('[data-toggle="tooltip"]').tooltip();
    };

    // public api
    return {
        initialize: initialize,
        doSrs: doSrs
    };

});
