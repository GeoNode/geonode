repositoryModule.factory('layerRepository', [
    '$http', 'urlResolver', 'dirtyManager', '$window', 'surfFeatureFactory', '$q', '$window', '$cookies',
    function($http, urlResolver, dirtyManager, $window, surfFeatureFactory, $q, $window, $cookies) {
        return {

            getFids: function(layerId) {
                return $http.get(urlResolver.resolveLayer('GetFids', { layerId: layerId }));
            },
            downloadData: function(layerId) {
                $window.open(urlResolver.resolveMap("DownloadLayerData", { layerId: layerId }));
            },
            saveAttributeDefinitions: function(layerId, attributeDefinitions) {
                return $http.post(urlResolver.resolveLayer('SaveAttributeDefinitions'), { layerId: layerId, attributeDefinitions: attributeDefinitions }).success(function() {
                    dirtyManager.setDirty(true);
                });
            },
            saveProperties: function(layerId, layerName, zoomLevel, properties, sldStyle, selectionStyleSld, labelingSld, callBack) {
                //old
                return $http.put('/layers/' + layerName + '/style/', {
                    LayerId: layerId,
                    Name: layerName,
                    ZoomLevel: zoomLevel,
                    StyleString: angular.toJson(properties),
                    SldStyle: sldStyle,
                    SelectionStyleSld: selectionStyleSld,
                    LabelingSld: labelingSld
                }, {
                    headers: {
                        'X-CSRFToken': $cookies.get('csrftoken')
                    }
                }).success(function() {
                    dirtyManager.setDirty(true);
                    if (callBack) {
                        callBack();
                    }
                });
            },
            // saveProperties: function(layerId, layerName, zoomLevel, properties, sldStyle, selectionStyleSld, labelingSld, callBack) {
            //     //new
            //     return $http.put('/gs/rest/styles/' + properties.Name + '.xml', sldStyle, {
            //         headers: {
            //             'X-CSRFToken': $cookies.get('csrftoken')
            //         }
            //     }).success(function() {
            //         dirtyManager.setDirty(true);
            //         if (callBack) {
            //             callBack();
            //         }
            //     });
            // },
            getAttributeValues: function(layerId, attributeId) {
                return $http.get(urlResolver.resolveClassification('GetAttributeValues', {
                    layerId: layerId,
                    attributeId: attributeId
                }));
            },
            getColumnValues: function(layerId, attributeId) {
                return $http.get(urlResolver.resolveClassification('GetColumnValues', {
                    layerId: layerId,
                    attributeId: attributeId
                }));
            },
            getAttributeGridData: function(dataRetrievalInfo, surfLayer) {
                return surfFeatureFactory.getFeatureFromUrl(urlResolver.resolveGeoServer('wfs', dataRetrievalInfo), surfLayer);
            },

            getNumberOfFeatures: function(dataId) {
                return $http.get(urlResolver.resolveCatalog('GetNumberOfFeatures', { dataId: dataId }));
            },
            saveClassifierDefinitions: function(layerId, classifierDefinitions, sldStyle, defaultStyleConditionalSld) {
                return $http.post(urlResolver.resolveClassification('SaveClassifierDefinitions'), {
                    layerId: layerId,
                    classifierDefinitions: classifierDefinitions ? angular.toJson(classifierDefinitions) : null,
                    attributeId: classifierDefinitions.selectedField,
                    sldStyle: sldStyle,
                    defaultStyleConditionalSld: defaultStyleConditionalSld
                }).success(function() {
                    dirtyManager.setDirty(true);
                });
            },
            updateLayerExtent: function(surfLayer) {
                return $http.get(urlResolver.resolveCatalog('GetDataExtent', { dataId: surfLayer.DataId })).success(function(layerExtent) {
                    surfLayer.setMapExtent(layerExtent);
                });
            },
            getUniqueClassesWithCount: function(layerId, attributeId) {
                return $http.get(urlResolver.resolveClassification('GetUniqueValuesForField', { layerId: layerId, attributeId: attributeId }));
            },
            getRangeClassesWithCount: function(layerId, attributeId, ranges) {
                return $http.post(urlResolver.resolveClassification('GetCountForRanges'), { layerId: layerId, attributeId: attributeId, ranges: ranges });
            },
            getNewGuid: function() {
                return $http.get(urlResolver.resolveCatalog('GetNewGuid'));
            },
            uploadDataFile: function(url) {
                return $http.get(url);
            },
            createDataFromShapeFiles: function(fileName, dataName, canceler) {
                return $http.post(urlResolver.resolveCatalog('CreateDataFromShpFile', { fileId: fileName, fileName: dataName }), { timeout: canceler.promise });
            },
            clearFeatures: function(layerId) {
                return $http.post(urlResolver.resolveLayer("SaveDeleteAllShapes"), { layerId: layerId }).success(function() {
                    dirtyManager.setDirty(true);
                });
            },
            saveVisualizationSettings: function(layerId, settings, sldStyle) {
                if (settings !== null) {
                    settings = angular.toJson(settings);
                }
                return $http.post(urlResolver.resolveLayer("SaveVisualizationSettings"), { layerId: layerId, settings: settings, sldStyle: sldStyle });
            },
            getAttributeValueRange: function(layerId, attributeId) {
                return $http.post(urlResolver.resolveClassification("GetRangeForField"), { layerId: layerId, attributeId: attributeId });
            },
            getRasterBandValue: function(layerId) {
                return $http.post(urlResolver.resolveClassification("GetValueForRasterBand"), { layerId: layerId });
            },
            getRanges: function(dataId, attributeId, divisions, algorithm) {
                return $http.post(urlResolver.resolveClassification('GetRanges'), { dataId: dataId, attributeId: attributeId, divisions: divisions, algorithm: algorithm });
            },
            isSingleBanded: function(layerId) {
                return $http.post(urlResolver.resolveClassification("IsSingleBanded"), { layerId: layerId });
            },
            saveVisibility: function(layerId, isVisible) {
                return $http.post(urlResolver.resolveLayer("SaveVisibility"), { layerId: layerId, isVisible: isVisible });
            },
            getUniqueRasterValues: function(layerId) {
                return $http.post(urlResolver.resolveClassification("GetUniqueRasterValues"), { layerId: layerId });
            },
            makeLayerEdited: function(layerId) {
                return $http.get(urlResolver.resolveLayer("MakeLayerDirty", { layerId: layerId })).then(function() {
                    dirtyManager.setDirty(true);
                });
            },
            getLayerByName: function(name) {
                return $q(function(resolve, reject) {
                    $http.get('/layers/' + name + '/get').then(function(res) {
                        resolve(res.data);
                    }, function(res) {
                        reject(res);
                    })
                });
            },
            getLayers: function(url) {
                // http://172.16.0.237:8000/proxy/?url=http%3A%2F%2F172.16.0.247%3A8080%2Fgeoserver%2Fwms%3Faccess_token%3D9df608bcabe911e7a833080027252357%26SERVICE%3DWMS%26REQUEST%3DGetCapabilities%26TILED%3Dtrue%26AcceptFormats%3D

                var x2js = new X2JS();

                return $q(function(resolve, reject) {
                    $http.get('/proxy/?url=' + encodeURIComponent(url)).then(function(res) {
                        resolve(x2js.xml_str2json(res.data));
                    }, function(res) {
                        reject(res);
                    });
                });
            },
            get: function(url) {
                var deferred = $q.defer();
                $http.get(url)
                    .success(function(res) {
                        deferred.resolve(res);
                    }).error(function(error, status) {
                        deferred.reject({ error: error, status: status });
                    });
                return deferred.promise;
            },
            getWMS: function(url, params) {
                var options = {
                    service: "wms",
                    version: "1.1.1",
                    request: "getfeatureinfo",
                    format: "image/jpeg",
                    transparent: true,
                    query_layers: "nurc:Arc_Sample",
                    styles: '',
                    layers: "nurc:Arc_Sample",
                    info_format: "application/json",
                    feature_count: 1,
                    srs: "epsg:3857",
                };
                for (var k in params) {
                    options[k] = params[k];
                }
                url = url || $window.GeoServerHttp2Root + options.query_layers.split(':')[0] + "/wms?";
                for (var k in options) {
                    url += '&' + k + '=' + options[k];
                }
                var uri = encodeURIComponent(url);
                return this.get('/proxy/?url=' + uri);

            },
        };
    }
]);