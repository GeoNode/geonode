appModule.factory('uploadDataService', ['layerRepository', 'catalogDataService', 'surfToastr', 'urlResolver', '$http',
    function (layerRepository, catalogDataService, surfToastr, urlResolver, $http) {

        var factory = {
            getNewGuid: function() {
                return layerRepository.getNewGuid();
            },
            cancelFileUpload: function(fileId) {
                return $http.post(urlResolver.resolveCatalog('CancelFileUpload'), { fileId: fileId });
            },
            createShapefileDataWithEpsgCode: function (fileId, fileName, epsgCode) {
                return $http.post(urlResolver.resolveCatalog('CreateDataFromShpFileWithEpsgCode'), {
                    fileId: fileId,
                    fileName: fileName,
                    epsg: epsgCode
                });
            },
            createDataFromTiffFileWithEpsgCode: function (fileId, fileName, epsgCode) {
                return $http.post(urlResolver.resolveCatalog('CreateDataFromTiffFileWithEpsgCode'), {
                    fileId: fileId,
                    fileName: fileName,
                    epsg: epsgCode
                });
            },
            createDataFromPdfFileWithEpsgCode: function (fileId, fileName, epsgCode) {
                return $http.post(urlResolver.resolveCatalog('CreateDataFromPdfFileWithEpsgCode'), {
                    fileId: fileId,
                    fileName: fileName,
                    epsg: epsgCode
                });
            },
            getFilesSize: function (files) {
                var totalSize = 0;
                for (var i = 0; i < files.length; i++) {
                    var currentFileSize = files[i].size;
                    totalSize += currentFileSize;
                }
                return totalSize;
            },
            createShapeData: function (fileName, dataName, canceler) {
                return layerRepository.createDataFromShapeFiles(fileName, dataName, canceler);
            },
            uploadDataFile: function (url) {
                return layerRepository.uploadDataFile(url);
            },
            dataNameExists: function (fileName) {
                var folders = catalogDataService.getData();
                var myfiles = folders[0].files;

                for (var i = 0; i < myfiles.length; i++) {
                    if (myfiles[i].Name == fileName) return true;
                }
                return false;
            },
            filterFiles: function (selectedFileType) {
                var queue = selectedFileType.uploader.queue;
                var fileExtension, requiredExtensions = {};

                removeDuplicateExtensionFiles(selectedFileType.uploader);

                for (var i in queue) {
                    fileExtension = getFileExtension(queue[i].file.name);
                    if (fileExtension) {
                        fileExtension = fileExtension.toLowerCase();
                    }
                    if (_.findWhere(selectedFileType.requiredFileExtensions, fileExtension)) {
                        requiredExtensions[fileExtension] = true;
                    } else if (!_.findWhere(selectedFileType.allowedFileExtensions, fileExtension)) {
                        queue[i].remove();
                    }
                }
                if (Object.keys(requiredExtensions).length == selectedFileType.requiredFileExtensions.length) {

                    return true && allNamesAreSame(selectedFileType.uploader);
                }
                return false;
            },
            getAllSelectedFiles: function (uploader) {
                var files = [];
                for (var i in uploader.queue) {
                    files.push(uploader.queue[i]._file);
                }
                return files;
            },
            getAbsoluteFileName: function (fileName) {
                var splitedName = fileName.split('.');
                splitedName.pop();
                var absoluteFileName = "";
                for (var i = 0; i < splitedName.length; i++) {
                    if (i == 0) {
                        absoluteFileName = splitedName[i];
                    }
                    else {
                        absoluteFileName = absoluteFileName + '.' + splitedName[i];
                    }
                }
                return absoluteFileName;
            },
            getAddressFilePostObject: function(fileName, columnInfo) {
                var postObject = {
                    fileName: fileName,
                    useFirstRowAsHeader: columnInfo.useFirstRowAsHeader
                };
                for (var i in columnInfo.mappings) {
                    var keyPrefix = 'mappings[' + i + '].';
                    postObject[keyPrefix + 'mappedName'] = columnInfo.mappings[i].name;
                    postObject[keyPrefix + 'nameInFile'] = columnInfo.mappings[i].nameInFile;
                    postObject[keyPrefix + 'index'] = columnInfo.mappings[i].index || -1;
                }
                return postObject;
            }
        }

        function removeDuplicateExtensionFiles(uploader) {
            var uniqueFiles = {};

            for (var i = uploader.queue.length - 1; i >= 0; i--) {
                if (uniqueFiles[getFileExtension(uploader.queue[i].file.name)]) {
                    uploader.queue[i].remove();
                    i--;
                } else {
                    uniqueFiles[getFileExtension(uploader.queue[i].file.name)] = true;
                }
            }
        }

        function getFileExtension(filename) {
            return '.' + filename.substr((~-filename.lastIndexOf(".") >>> 0) + 2);
        }

        function validExtension(requiredExtensions, filename) {
            var fileExtension = getFileExtension(filename);
            return !!_.findWhere(requiredExtensions, fileExtension);
        }

        function allNamesAreSame(uploader) {
            var name = {};
            for (var i in uploader.queue) {
                name[factory.getAbsoluteFileName(uploader.queue[i].file.name)] = true;
            }
            if (Object.keys(name).length == 1) return true;
            else {
                surfToastr.error("All files must have same name.");
                uploader.clearQueue();
                return false;
            }
        }

        return factory;
    }
]);