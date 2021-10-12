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
        initUploadProgressTable,
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

    initUploadProgressTable = function() {
        const section = document.querySelector('#incomplete-download-list');
        const removeModal = section.querySelector('#remove-incomplete-upload-modal');
        const table = section.querySelector('.upload-progress-table');
        const tbody = table.querySelector('tbody');
        const prevPage = section.querySelector('.upload-progress-prev-page');
        const nextPage = section.querySelector('.upload-progress-next-page');
        const progressPage = section.querySelector('.upload-progress-page');
        const currentPage = progressPage.querySelector('.upload-progress-page-count');
        const totalPages = progressPage.querySelector('.upload-progress-page-total');
        const resumeTooltip = table.getAttribute('data-resume-tool-tooltip');
        const removeTooltip = table.getAttribute('data-remove-tool-tooltip');
        const successTooltip = table.getAttribute('data-success-tool-tooltip');
        const invalidTooltip = table.getAttribute('data-invalid-tool-tooltip');
        const removeModalButton = removeModal && removeModal.querySelector('.remove-incomplete-upload-modal-button');
        const removeModalName = removeModal && removeModal.querySelector('.remove-incomplete-upload-modal-name');

        const intervalTime = 3000;

        var page = 1;
        var maxPage = 1;
        var pageSize = 10;
        var render;
        var selected = null;
        var processed = [];
        var lastUploadsIds = [];
        var uploads = [];
        var loading = false;

        function getUploadItems(options) {
            $.ajax({
                url: options.url || siteUrl + 'api/v2/uploads?filter{-state}=PROCESSED&page=1&page_size=99999',
                async: false,
                mode: 'queue',
                contentType: false,
            })
                .done(function (response) {
                    if (options.resolve) {
                        options.resolve(response);
                    }
                })
                .fail(function (error) {
                    if (options.reject) {
                        options.reject(error);
                    }
                });
        }

        function handleDelete(options) {
            $.ajax({
                url: options.url,
                async: false,
                mode: 'queue',
                contentType: false,
            })
                .done(function () {
                    if (render) {
                        render(true);
                    }
                })
                .fail(function () {});
        }

        function progressBar(properties) {
            properties.parent.style.position = 'relative';
            // add a small progress bar in the progressNode
            const progressBarBg = document.createElement('div');
            progressBarBg.style.position = 'absolute';
            progressBarBg.style.left = 0;
            progressBarBg.style.bottom = 0;
            progressBarBg.style.width = '100%';
            progressBarBg.style.height = '4px';
            progressBarBg.style.backgroundColor = '#f2f2f2';
            properties.parent.appendChild(progressBarBg);

            const progressBar = document.createElement('div');
            progressBar.style.position = 'absolute';
            progressBar.style.left = 0;
            progressBar.style.bottom = 0;
            progressBar.style.width = properties.width;
            progressBar.style.height = '4px';
            progressBar.style.transition = '0.3s width';
            progressBar.style.backgroundColor = '#27ca3b';
            properties.parent.appendChild(progressBar);
        }

        function tableRow(properties) {
            const row = document.createElement('tr');
            row.setAttribute('data-upload-id', properties.id);
            tbody.appendChild(row);

            const name = document.createElement('td');
            name.innerHTML = properties.state === 'PROCESSED' && properties.detail_url
                ? '<a href="' + properties.detail_url + '" target="_blank" rel="noopener noreferrer">' + properties.name + '</a>'
                : properties.name;
            row.appendChild(name);

            const date = document.createElement('td');
            date.innerHTML = properties.create_date
                ? new Date(properties.create_date).toLocaleString()
                : 'none';
            row.appendChild(date);

            const progressPercentage = Math.round(properties.progress) + '%';
            const progress = document.createElement('td');
            progress.innerHTML = progressPercentage;
            row.appendChild(progress);
            progressBar({ parent: progress, width: progressPercentage });

            switch(properties.state) {
                case 'PENDING':
                    progress.setAttribute('class', 'warning');
                    break;
                case 'PROCESSED':
                    progress.setAttribute('class', 'success');
                    break;
                case 'INVALID':
                    progress.setAttribute('class', 'danger');
                    break;
                default:
                    break;
            }

            const infoTools = document.createElement('td');
            infoTools.setAttribute('class', 'text-center');
            infoTools.style.verticalAlign = 'middle';
            infoTools.style.minWidth = '60px';
            infoTools.style.height = '50px';
            row.appendChild(infoTools);

            if (properties.resume_url) {
                const resumeTool = document.createElement('button');
                resumeTool.setAttribute('class', 'btn btn-default btn-sm incomplete-resume');
                resumeTool.setAttribute('title', resumeTooltip);
                resumeTool.setAttribute('data-toggle', 'tooltip');
                resumeTool.setAttribute('data-placement', 'top');
                resumeTool.innerHTML = '<i class="fa fa-play"></i>';
                resumeTool.onclick = function () { window.location = properties.resume_url; };
                infoTools.appendChild(resumeTool);
                $(resumeTool).tooltip();
            } else {
                const infoIcon = document.createElement('i');
                if (properties.state === 'COMPLETE') {
                    infoIcon.setAttribute('class', 'fa fa-spinner fa-spin');
                }
                if (properties.state === 'PROCESSED') {
                    infoIcon.setAttribute('data-toggle', 'tooltip');
                    infoIcon.setAttribute('data-placement', 'top');
                    infoIcon.setAttribute('title', successTooltip);
                    infoIcon.setAttribute('class', 'fa fa-check-circle text-success');
                }
                if (properties.state === 'INVALID') {
                    infoIcon.setAttribute('data-toggle', 'tooltip');
                    infoIcon.setAttribute('data-placement', 'top');
                    infoIcon.setAttribute('title', invalidTooltip);
                    infoIcon.setAttribute('class', 'fa fa-exclamation-circle text-danger');
                }
                infoTools.appendChild(infoIcon);
                $(infoIcon).tooltip();
            }

            const removeTools = document.createElement('td');
            removeTools.setAttribute('class', 'text-center');
            removeTools.style.minWidth = '60px';
            removeTools.style.height = '50px';
            removeTools.style.verticalAlign = 'center';
            row.appendChild(removeTools);

            const removeTool = document.createElement('button');
            removeTool.innerHTML = '<i class="fa fa-remove"></i>';
            removeTool.setAttribute('class', 'btn btn-danger btn-sm incomplete-remove');
            removeTool.setAttribute('title', removeTooltip);
            removeTool.setAttribute('data-toggle', 'tooltip');
            removeTool.setAttribute('data-placement', 'top');
            if (removeModal && properties.delete_url) {
                removeTool.onclick = function() {
                    removeModalName.innerHTML = properties.name;
                    $(removeModal).modal();
                    selected = { id: properties.id, url: properties.delete_url };
                };
            } else {
                removeTool.setAttribute('disabled', true);
                removeTool.setAttribute('class', 'btn btn-default btn-sm incomplete-remove');
            }
            removeTools.appendChild(removeTool);
            $(removeTool).tooltip();

        }

        render = function(request) {

            loading = true;

            function updateRenderedNodes() {

                tbody.innerHTML = '';
                var start = (page - 1) * pageSize;
                var end = start + pageSize;
                var items = [].concat(uploads).concat(processed);

                items.sort(function(a, b) {
                    return (a.create_date < b.create_date)
                        ? 1
                        : ((a.create_date > b.create_date)
                            ? -1
                            : 0)
                });

                maxPage = Math.ceil(items.length / pageSize);

                for (var i = start; i < end; i++) {
                    if (items[i]) {
                        tableRow(items[i]);
                    }
                }
                const prevLink = page > 1;
                const nextLink = page < maxPage;

                prevPage.setAttribute('class', !prevLink ? 'disabled' : '');
                nextPage.setAttribute('class', !nextLink ? 'disabled' : '');
                prevPage.style.cursor = !prevLink ? 'not-allowed' : 'pointer';
                nextPage.style.cursor = !nextLink ? 'not-allowed' : 'pointer';

                progressPage.style.display = 'inline';
                currentPage.innerHTML = page;
                totalPages.innerHTML = maxPage;

                section.style.display = items.length === 0 ? 'none' : 'block';
                loading = false;
            }

            if (request) {
                getUploadItems({
                    resolve: function(response) {

                        uploads = response.uploads || [];
                        
                        // in case the upload ID is already present in the processed list
                        // is removed from the processed in order to avoid row duplication
                        // row duplication usually occours with async flow activated
                        var processedCopy = [...processed]

                        for (var i in uploads) {
                            for (var j in processed) {
                                if (uploads[i].id == processed[j].id) {
                                    processedCopy.splice(i, 1)
                                }
                            }
                        }

                        processed = [...processedCopy]

                        var currentUploadIds = [];
                        for (var i = 0; i < uploads.length; i++) {
                            currentUploadIds.push(uploads[i].id);
                        }
    
                        var diffUploadIds = [];
                        for (var i = 0; i < lastUploadsIds.length; i++) {
                            if (currentUploadIds.indexOf(lastUploadsIds[i]) === -1) {
                                diffUploadIds.push(lastUploadsIds[i]);
                            }
                        }

                        lastUploadsIds = currentUploadIds;

                        if (diffUploadIds.length > 0) {
                            // to avoid to request all the processed uploads
                            // we need to filter only on the ones detected by the difference
                            var idFilters = '';
                            for (var i = 0; i < diffUploadIds.length; i++) {
                                idFilters += '&filter{id.in}=' + diffUploadIds[i];
                            }
                            getUploadItems({
                                url: siteUrl + 'api/v2/uploads?filter{state}=PROCESSED&page=1&page_size=99999' + idFilters,
                                resolve: function(res) {
                                    const processedUploads = res.uploads || [];
                                    for (var i = 0; i < processedUploads.length; i++) {
                                        if (diffUploadIds.indexOf(processedUploads[i].id) !== -1) {
                                            processed.push(processedUploads[i]);
                                        }
                                    } 
                                    updateRenderedNodes();
                                },
                                reject: function() {
                                    updateRenderedNodes();
                                }
                            });
                        } else {
                            updateRenderedNodes();
                        }
                    },
                    reject: function(error) {
                        // if does not find the page
                        // reset to page 1
                        // this could happen while deleting the last item in a page
                        if (error.status === 404) {
                            page = 1;
                            if (render) {
                                render(true);
                            }
                        }
                        loading = false;
                    }
                });
            } else {
                updateRenderedNodes();
            }
        }

        if (removeModal) {
            $(removeModal).on('hide.bs.modal', function (e) {
                selected = null;
            });
            removeModalButton.onclick = function () {
                handleDelete(selected);
                selected = null;
                $(removeModal).modal('hide');
            };
        }
        prevPage.addEventListener('click', function() {
            const prev = page - 1;
            if (prev >= 1) {
                page = prev;
                render();
            }
        });
        nextPage.addEventListener('click', function() {
            const next = page + 1;
            if (next <= maxPage) {
                page = next;
                render();
            }
        });

        render(true);
        // continuously request update for the current page to the api
        // and re-render the table
        setInterval(function() {
            if (!loading) {
                render(true);
            }
        }, intervalTime);
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

        try {
            initUploadProgressTable();
        } catch (error) {
            console.log(error);
            // expected output: ReferenceError: nonExistentFunction is not defined
            // Note - error messages will vary depending on browser
        }
    };

    // public api
    return {
        initialize: initialize,
        doSrs: doSrs
    };

});
