appModule.controller("uploadDataController", [
    '$scope', '$compile', '$timeout', '$modalInstance', '$sce', 'surfToastr', 'subscriptionStatus', 'uploadDataService', 'FileUploader', 'urlResolver', '$q', '$modal',
    function ($scope, $compile, $timeout, $modalInstance, $sce, surfToastr, subscriptionStatus, uploadDataService, FileUploader, urlResolver, $q, $modal) {

        var guid, currentErrorMessage, canceler = $q.defer();

        $scope.resetInfo = function () {
            clearMessages();
            $scope.subscriptionExceeded = true;
            $scope.shapeTypeIsSupported = false;
            $scope.data = { name: '' };
        };

        $scope.resetInfo();

        uploadDataService.getNewGuid().success(function (data) {
            guid = data.guid;
        });

        $scope.uploadInProgress = function () {
            return $scope.selected.file.uploader.progress == 100 || $scope.selected.file.uploader.isUploading;
        };

        function showEpsgCodeOptions(epsgResult, onSelect) {
            $modalInstance.close();
            $modal.open({
                templateUrl: '/static/Templates/CatalogBrowser/selectEpsgCode.html',
                controller: 'selectEpsgCodeController',
                backdrop: 'static',
                keyboard: false,
                resolve: {
                    epsgCodes: function () {
                        return epsgResult.codes;
                    },
                    onSelect: function () {
                        return onSelect;
                    },
                    fileId: function () {
                        return guid;
                    },
                    fileName: function () {
                        return $scope.data.name;
                    }
                }
            }).result.then(function (data) {
                if (data && data.success) {
                    surfToastr.success(appMessages.toastr.dataUploaded());
                    addDataToCatalog(data);
                } else {
                    surfToastr.error("Uploading failed.");
                    uploadDataService.cancelFileUpload(guid);
                }
            }, function () {
                uploadDataService.cancelFileUpload(guid);
            });
        };

        //https://github.com/nervgh/angular-file-upload/wiki/Module-API
        $scope.fileTypes = [
            {
                label: 'Shape File',
                requiredFileExtensions: ['.shp', '.dbf', '.prj', '.shx'],
                allowedFileExtensions: ['.shp', '.dbf', '.prj', '.shx', '.surfgis'],
                type: 'shape',
                warningMessage: null,
                uploader: new FileUploader({
                    onCompleteAll: function () {
                        uploadDataService.createShapeData(guid, $scope.data.name, canceler).success(function (data) {
                            if (data.success) {
                                addDataToCatalog(data);
                            } else if (data.epsgResult) {
                                showEpsgCodeOptions(data.epsgResult, uploadDataService.createShapefileDataWithEpsgCode);
                            } else {
                                surfToastr.error("One or more required file/s missing.");
                                onUploadError();
                            }
                        }).error(function () {
                            surfToastr.error("Uploading failed.");
                            onUploadError();
                        });
                    },
                    onBeforeUploadItem: function (item) {
                        item.formData.push({ fileId: guid });
                    },
                    url: urlResolver.resolveCatalog("UploadShpFile")
                }),
                filterFiles: uploadDataService.filterFiles
            },
            {
                label: 'Zipped Shape File',
                requiredFileExtensions: ['.zip'],
                allowedFileExtensions: ['.zip'],
                type: 'zip',
                warningMessage: null,
                uploader: new FileUploader({
                    onErrorItem: function () {
                        surfToastr.error("Uploading failed.");
                        onUploadError();
                    },
                    onSuccessItem: function (response, data) {
                        if (data.success) {
                            addDataToCatalog(data);
                        } else if (data.epsgResult) {
                            guid = data.fileId;
                            showEpsgCodeOptions(data.epsgResult, uploadDataService.createShapefileDataWithEpsgCode);
                        } else {
                            surfToastr.error("Invalid File format.");
                            onUploadError();
                        }
                    },
                    onBeforeUploadItem: function (item) {
                        item.formData.push({ fileName: $scope.data.name });
                    },
                    url: urlResolver.resolveCatalog("CreateDataFromZippedShpFile")
                }),
                filterFiles: uploadDataService.filterFiles
            },
            {
                label: 'Address File (only for US)',
                requiredFileExtensions: ['.csv'],
                allowedFileExtensions: ['.csv'],
                type: 'address',
                warningMessage: null,
                uploader: new FileUploader({
                    onErrorItem: function () {
                        surfToastr.error("Uploading failed.");
                        onUploadError();
                    },
                    onSuccessItem: function (response, data) {
                        if (data.success) {
                            addDataToCatalog(data);
                            if (data.unresolvedAddresses && data.unresolvedAddresses.length > 0) {
                                showUnresolvedAddresses(data.unresolvedAddresses);
                            }
                        } else {
                            surfToastr.error("Invalid file format.");
                            onUploadError();
                        }
                    },
                    onBeforeUploadItem: function (item) {
                        item.formData.push(uploadDataService.getAddressFilePostObject($scope.data.name, extractedCsvColumnInfo));
                    },
                    url: urlResolver.resolveCatalog("CreateDataFromAddressFile")
                }),
                filterFiles: uploadDataService.filterFiles
            },
            {
                label: 'Raster Data (GeoTIFF)',
                requiredFileExtensions: ['.zip'],
                allowedFileExtensions: ['.zip'],
                type: 'zip',
                warningMessage: $sce.trustAsHtml("Data (.tif/.tiff) should be zipped before uploading."),
                uploader: new FileUploader({
                    onErrorItem: function () {
                        surfToastr.error("Uploading failed.");
                        onUploadError();
                    },
                    onSuccessItem: function (response, data) {
                        if (data.success) {
                            addDataToCatalog(data);
                        } else if (data.epsgResult) {
                            guid = data.fileId;
                            showEpsgCodeOptions(data.epsgResult, uploadDataService.createDataFromTiffFileWithEpsgCode);
                        } else {
                            surfToastr.error("Invalid File format.");
                            onUploadError();
                        }
                    },
                    onBeforeUploadItem: function (item) {
                        item.formData.push({ fileName: $scope.data.name });
                    },
                    url: urlResolver.resolveCatalog("CreateDataFromZippedTiffFile")
                }),
                filterFiles: uploadDataService.filterFiles
            },
            /*{
                label: 'GeoPDF',
                requiredFileExtensions: ['.pdf'],
                allowedFileExtensions: ['.pdf'],
                type: 'pdf',
                warningMessage: null,
                uploader: new FileUploader({
                    onErrorItem: function () {
                        surfToastr.error("Uploading failed.");
                        onUploadError();
                    },
                    onSuccessItem: function (response, data) {
                        if (data.success) {
                            addDataToCatalog(data);
                        } else if (data.epsgResult) {
                            guid = data.fileId;
                            showEpsgCodeOptions(data.epsgResult, uploadDataService.createDataFromPdfFileWithEpsgCode);
                        } else {
                            surfToastr.error("Invalid File format.");
                            onUploadError();
                        }
                    },
                    onBeforeUploadItem: function (item) {
                        item.formData.push({ fileName: $scope.data.name });
                    },
                    url: urlResolver.resolveCatalog("CreateDataFromPdfFile")
                }),
                filterFiles: uploadDataService.filterFiles
            },*/
            {
                label: 'CSV File',
                requiredFileExtensions: ['.csv'],
                allowedFileExtensions: ['.csv'],
                type: 'csv',
                warningMessage: null,
                uploader: new FileUploader({
                    onErrorItem: function () {
                        surfToastr.error("Uploading failed.");
                        onUploadError();
                    },
                    onSuccessItem: function (response, data) {
                        if (data.success) {
                            addDataToCatalog(data);
                        } else {
                            surfToastr.error("Invalid file format.");
                            onUploadError();
                        }
                    },
                    onBeforeUploadItem: function (item) {
                        item.formData.push({ fileName: $scope.data.name });
                    },
                    url: urlResolver.resolveCatalog("CreateDataFromCsvFile")
                }),
                filterFiles: uploadDataService.filterFiles
            }
        //,{
        //    label: 'FileGDB',
        //    requiredFileExtensions: ['.zip'],
        //    type: 'gdb',
        //    uploader: new FileUploader({
        //        onErrorItem: function (fileItem, response, status, headers) {
        //            surfToastr.error("Uploading failed.");
        //            onUploadError();
        //        },
        //        onSuccessItem: function (response, data, status, headers) {
        //            if (data.success) {
        //                addDataToCatalog(data);
        //            } else {
        //                surfToastr.error("Invalid File format.");
        //                onUploadError();
        //            }
        //        },
        //        onBeforeUploadItem: function (item) {
        //            item.formData.push({ fileName: $scope.data.name });
        //        },
        //        url: urlResolver.resolveCatalog("CreateDataFromZippedGdbFile")
        //    }),
        //    filterFiles: uploadDataService.filterFiles
        //},
        //{
        //    label: 'GeoJSON',
        //    requiredFileExtensions: ['.json'],
        //    type: 'json',
        //    uploader: new FileUploader({
        //        onErrorItem: function (fileItem, response, status, headers) {
        //            surfToastr.error("Uploading failed.");
        //            onUploadError();
        //        },
        //        onSuccessItem: function (response, data, status, headers) {
        //            if (data.success) {
        //                addDataToCatalog(data);
        //            } else {
        //                surfToastr.error("Invalid File format.");
        //                onUploadError();
        //            }
        //        },
        //        onBeforeUploadItem: function (item) {
        //            item.formData.push({ fileName: $scope.data.name });
        //        },
        //        url: urlResolver.resolveCatalog("CreateDataFromFile")
        //    }),
        //    filterFiles: uploadDataService.filterFiles
        //},
        //{
        //    label: 'GPX',
        //    requiredFileExtensions: ['.gpx'],
        //    type: 'gpx',
        //    uploader: new FileUploader({
        //        onErrorItem: function (fileItem, response, status, headers) {
        //            surfToastr.error("Uploading failed.");
        //            onUploadError();
        //        },
        //        onSuccessItem: function (response, data, status, headers) {
        //            if (data.success) {
        //                addDataToCatalog(data);
        //            } else {
        //                surfToastr.error("Invalid File format.");
        //                onUploadError();
        //            }
        //        },
        //        onBeforeUploadItem: function (item) {
        //            item.formData.push({ fileName: $scope.data.name });
        //        },
        //        url: urlResolver.resolveCatalog("CreateDataFromFile")
        //    }),
        //    filterFiles: uploadDataService.filterFiles
        //},
        //{
        //    label: 'GML',
        //    requiredFileExtensions: ['.gml'],
        //    type: 'gml',
        //    uploader: new FileUploader({
        //        onErrorItem: function (fileItem, response, status, headers) {
        //            surfToastr.error("Uploading failed.");
        //            onUploadError();
        //        },
        //        onSuccessItem: function (response, data, status, headers) {
        //            if (data.success) {
        //                addDataToCatalog(data);
        //            } else {
        //                surfToastr.error("Invalid File format.");
        //                onUploadError();
        //            }
        //        },
        //        onBeforeUploadItem: function (item) {
        //            item.formData.push({ fileName: $scope.data.name });
        //        },
        //        url: urlResolver.resolveCatalog("CreateDataFromFile")
        //    }),
        //    filterFiles: uploadDataService.filterFiles
        //}
        ];

        $scope.containsRequiredFiles = false;
        var extractedCsvColumnInfo;
        $scope.$watch('selected.file.uploader.queue.length', function () {
            if ($scope.selected.file.uploader.queue.length == 0) {
                $scope.data.name = "";
            }
            clearMessages();
            if ($scope.selected.file.filterFiles($scope.selected.file)) {
                $scope.containsRequiredFiles = true;
                $scope.data.name = uploadDataService.getAbsoluteFileName($scope.selected.file.uploader.queue[0].file.name);
                $scope.nameField.focused = true;
                showSubscriptionValidations();
                if ($scope.selected.file.type == 'shape') {
                    validateShapeFileType(uploadDataService.getAllSelectedFiles($scope.selected.file.uploader));
                } else if ($scope.selected.file.type == 'address') {
                    openAddressFileMappingDialog();
                }
            } else {
                $scope.containsRequiredFiles = false;
            }
        });

        function clearMessages() {
            $scope.warningMessage = null;
            $scope.errorMessage = null;
            $scope.uploadButtonText = null;
            currentErrorMessage = null;
        }

        $scope.selected = {
            file: $scope.fileTypes[0]
        };

        function showUnresolvedAddresses(addresses) {
            var text = "";
            for (var i in addresses) {
                text += ("<p>" + addresses[i] + "</p>");
            }
            dialogBox.multiAction({
                title: "Unresolved Addresses",
                text: text,
                actions: {
                    Close: function () {
                    }
                },
                canCancel: false,
                width: '550px',
                resizable: false
            });
        }

        function openAddressFileMappingDialog() {
            $('#upload-form-container').hide();
            $modal.open({
                templateUrl: '/static/Templates/CsvHeaderMapping.html',
                controller: 'csvHeaderMappingController',
                backdrop: 'static',
                keyboard: false,
                resolve: {
                    file: function () {
                        return $scope.selected.file.uploader.queue[0]._file;
                    }
                }
            }).result.then(function (columnInfo) {
                if (columnInfo) {
                    extractedCsvColumnInfo = columnInfo;
                } else {
                    $scope.selected.file.uploader.clearQueue();
                }
                $('#upload-form-container').show();
            });
        }

        function showWarning(message) {
            $scope.warningMessage = $sce.trustAsHtml(message);
        }

        function showError(message) {
            $scope.errorMessage = $sce.trustAsHtml(message);
            currentErrorMessage = message;
        }

        $scope.nameField = { focused: true };

        function showSubscriptionValidations() {
            var files = uploadDataService.getAllSelectedFiles($scope.selected.file.uploader);

            if (files.length == 0) return;
            var totalSize = uploadDataService.getFilesSize(files);

            var message;
            $scope.subscriptionExceeded = false;
            if (message = subscriptionStatus.validateInBandwidthLimit(totalSize)) {
                $scope.subscriptionExceeded = true;
            } else if (message = subscriptionStatus.validateTotalStorageLimit(totalSize)) {
                $scope.subscriptionExceeded = true;
            }
            if (message) {
                showError(message);
            }
        }

        $scope.formSubmissionDisabled = function () {
            return !$scope.data.name || !$scope.containsRequiredFiles || $scope.subscriptionExceeded
                   || $scope.selected.file.uploader.isUploading || !guid
                   || $scope.selected.file.uploader.progress == 100 || $scope.errorMessage;
        }

        $scope.dataNameChanged = function () {
            var duplicateName = "File with the same name already exists, please choose a different name.";
            if (uploadDataService.dataNameExists($scope.data.name)) {
                showError(duplicateName);
                $scope.nameField.focused = true;
            } else {
                if (currentErrorMessage == duplicateName) {
                    $scope.errorMessage = null;
                    currentErrorMessage = null;
                }
            }
        };

        $scope.submitForm = function () {
            $scope.dataNameChanged();
            if ($scope.formSubmissionDisabled()) return;
            clearMessages();
            $scope.selected.file.uploader.uploadAll();
        };

        function addDataToCatalog(response) {
            $scope.addFiles(response.data);
            $modalInstance.close();
            surfToastr.success(appMessages.toastr.dataUploaded());
            subscriptionStatus.increaseDataStorageUsageForUpload(response.fileSize);
        }

        $scope.closeModal = function (isFromCode) {
            if ($scope.uploadInProgress() && !isFromCode) {
                dialogBox.confirm({
                    title: appMessages.confirm.cancelUploadTitle,
                    text: appMessages.confirm.cancelUpload,
                    action: function () {
                        $scope.selected.file.uploader.cancelAll();
                        canceler.resolve();
                        $modalInstance.close();
                    }
                });
            } else {
                $modalInstance.close();
            }
        };

        function onUploadError() {
            canceler.resolve();
            $scope.selected.file.uploader.cancelAll();
            $scope.closeModal(true);
        }

        function validateShapeFileType(files) {
            function showConversionMessage(message) {
                $scope.shapeTypeIsSupported = true;
                $scope.uploadButtonText = "Upload and Convert";
                showWarning(message + "<br/>Are you sure you want to continue?");
                $scope.$apply();
            }
            if (!window.FileReader) {
                $scope.shapeTypeIsSupported = true;
                showWarning("If your shapefile contains multipart polylines, " +
                    "those will be converted to single part polylines.");
                return;
            }
            for (var i = 0; i < files.length; i++) {
                var name = files[i].name;
                if (name.indexOf('.shp', name.length - '.shp'.length) !== -1) {
                    var shapeFile = new Jantrik.GIS.ShapeFile(files[i]);
                    shapeFile.getHeader(function (header) {
                        var type = header.getShapeType();
                        switch (header.getShapeTypeCode()) {
                            case 1:
                            case 3:
                            case 5:
                                $scope.shapeTypeIsSupported = true;
                                break;
                            case 11:
                                showConversionMessage("This is a " + type + " shapefile. " +
                                    "This will be converted to a 2D point shapefile and " +
                                    "the Z and M values will be stored as attribute.");
                                break;
                            case 13:
                                showConversionMessage("This is a " + type + " shapefile. " +
                                    "This will be converted to a 2D Polyline shapefile and " +
                                    "the Z and M values will be <strong>lost</strong>.");
                                break;
                            case 15:
                                showConversionMessage("This is a " + type + " shapefile. " +
                                    "This will be converted to a 2D Polygon shapefile and " +
                                    "the Z and M values will be <strong>lost</strong>.");
                                break;
                            case 21:
                                showConversionMessage("This is a " + type + " shapefile. " +
                                    "This will be converted to a 2D point shapefile and " +
                                    "the M values will be stored as attribute.");
                                break;
                            case 23:
                                showConversionMessage("This is a " + type + " shapefile. " +
                                        "This will be converted to a 2D Polyline shapefile and " +
                                        "the M values will be <strong>lost</strong>.");
                                break;
                            case 25:
                                showConversionMessage("This is a " + type + " shapefile. " +
                                    "This will be converted to a 2D Polygon shapefile and " +
                                    "the M values will be <strong>lost</strong>.");
                                break;
                            default:
                                $scope.shapeTypeIsSupported = false;
                                showError("This is a " + type + " shapefile. This type is not supported by SurfGIS.");
                                break;
                        }
                        $scope.$apply();
                    });

                    break;
                }
            }
        }

    }]);
