appModule.factory('attributeGridService', ['layerRepository', 'featureService', 'surfFeatureFactory', 'mapService', 'mapAccessLevel',
    function (layerRepository, featureService, surfFeatureFactory, mapService, mapAccessLevel) {
        var deletedFids, editedRows;
        var image = new ol.style.Circle({
            radius: 5,
            fill: new ol.style.Fill({
                color: 'rgba(255,0,0,1.0)'
            }),
            stroke: new ol.style.Stroke({ color: 'rgba(255,0,0,1.0)', width: 3 })
        });
        var red = [255, 0, 0, 0.5];
        var green = [0, 255, 0, 0.5];
        var blue = [0, 0, 255, 0.5];
        var styles = {
            'Point': new ol.style.Style({
                image: new ol.style.Circle({
                  radius: 6,
                  stroke: new ol.style.Stroke({
                    color: 'white',
                    width: 2
                  }),
                  fill: new ol.style.Fill({
                    color: green
                  })
                })
              }),
            'LineString': new ol.style.Style({
                stroke: new ol.style.Stroke({
                    color: red,
                    width: 3
                })
            }),
            'MultiLineString': new ol.style.Style({
                stroke: new ol.style.Stroke({
                    color: red,
                    width: 3
                })
            }),
            'MultiPoint': new ol.style.Style({
                image: image
            }),
            'MultiPolygon': new ol.style.Style({
                stroke: new ol.style.Stroke({
                    color: green,
                    width: 3
                }),
                fill: new ol.style.Fill({
                    color: blue
                })
            }),
            'Polygon': new ol.style.Style({
                stroke: new ol.style.Stroke({
                    color: green,
                    lineDash: [4],
                    width: 3
                }),
                fill: new ol.style.Fill({
                    color: blue
                })
            }),
            'GeometryCollection': new ol.style.Style({
                stroke: new ol.style.Stroke({
                    color: red,
                    width: 3
                }),
                fill: new ol.style.Fill({
                    color: green
                }),
                image: new ol.style.Circle({
                    radius: 10,
                    fill: null,
                    stroke: new ol.style.Stroke({
                        color: red
                    })
                })
            }),
            'Circle': new ol.style.Style({
                stroke: new ol.style.Stroke({
                    color: red,
                    width: 3
                }),
                fill: new ol.style.Fill({
                    color: green
                })
            })
        };
        var styleFunction = function(feature) {
            return [styles[feature.getGeometry().getType()]];
        };
        var vectorSource = new ol.source.Vector();
        var vectorLayer = new ol.layer.Vector({
            source: vectorSource,
            style: styleFunction
        });
        
        var map = mapService.getMap();
        map.addLayer(vectorLayer);

        var factory = {
            resetAll: function () {
                deletedFids = [];
                editedRows = [];
            },
            highlightFeature : function(featureJson){
                var mapFeatures = (new ol.format.GeoJSON()).readFeatures(featureJson, { featureProjection: 'EPSG:3857' });
                vectorSource.addFeatures(mapFeatures);
                var extent = mapFeatures[0].getGeometry().getExtent();
                map.getView().fit(extent,map.getSize());
            },
            getNumberOfFeatures: function (layerId) {
                return layerRepository.getNumberOfFeatures(layerId);
            },
            dateValidator: function (value, callback) {
                if (!value || moment(value, "D MMM, YYYY", true).isValid()) {
                    callback(true);
                }
                else {
                    callback(false);
                }
            },
            getGridData: function (dataRetrievalInfo, surfLayer) {
                return layerRepository.getAttributeGridData(dataRetrievalInfo, surfLayer);
            },
            populateDataIntoGrid: function (grid, features) {
                grid.attributeRows.length = 0;
                features.map(function (feature) {
                    var surfFeature = feature.surfFeature;
                    grid.attributeRows.push({
                        Fid: surfFeature.getFid(),
                        Attributes: surfFeature.getAttributes(),
                        OpenlayerFeature: feature.olFeature
                    });
                });
            },
            changeEditedRows: function (gridData) {
                for (var j in editedRows) {
                    var editedItem = _.findWhere(gridData.attributeRows, { Fid: editedRows[j].Fid });
                    if (editedItem) {
                        editedItem.Attributes = angular.copy(editedRows[j].Attributes);
                        editedItem.isDirty = true;
                    }
                }
            },
            storeChanges: function (changes, data) {
                for (var i in changes) {
                    var row = data[changes[i][0]];
                    factory.populateEditedRows(row);
                }
            },
            populateEditedRows: function (currentEditedItem) {
                var editedItem = _.findWhere(editedRows, { Fid: currentEditedItem.Fid });
                if (editedItem) {
                    editedItem.Attributes = angular.copy(currentEditedItem.Attributes);
                } else {
                    editedRows.push({
                        Fid: currentEditedItem.Fid,
                        Attributes: angular.copy(currentEditedItem.Attributes),
                        OpenlayerFeature: currentEditedItem.OpenlayerFeature
                    });
                }
            },
            getFeaturesWithChangedAttributes: function (layerId) {
                var features = [];
                for (var index in editedRows) {
                    var olFeature = editedRows[index].OpenlayerFeature;
                    olFeature.setProperties(editedRows[index].Attributes);
                    var feature = surfFeatureFactory.createSurfFeature(olFeature, mapService.getLayer(layerId));
                    features.push(feature);
                }
                return features;
            },
            deleteRow: function (fid) {
                deletedFids.push(fid);
            },
            removeDeletedRows: function (gridData) {
                for (var i in deletedFids) {
                    var attributeRows = _.without(gridData.attributeRows, _.findWhere(gridData.attributeRows, { Fid: deletedFids[i] }));
                    gridData.attributeRows.length = 0;
                    for (var j in attributeRows) {
                        gridData.attributeRows.push(attributeRows[j]);
                    }
                }
            },
            removeDeletedFeatures: function (layerId) {
                if (deletedFids && deletedFids.length > 0) {
                    var surfLayer = mapService.getLayer(layerId);
                    featureService.deleteFeatures(deletedFids, surfLayer).success(function () {
                        surfLayer.refresh();
                    });
                }
            },
            haveFeaturesToDelete: function () {
                return deletedFids && deletedFids.length > 0;
            },
            hasSingleFeatureToDelete: function () {
                return deletedFids && deletedFids.length === 1;
            },
            getColumnHeaders: function (attributeDefinitions) {
                var headers = [];
                for (var i = 0; i < attributeDefinitions.length; i++) {
                    if (mapAccessLevel.isPublic && !attributeDefinitions[i].IsPublished) continue;

                    headers.push(attributeDefinitions[i].Name);
                }
                return headers;
            },
            getColumns: function (attributeDefinitions, attributeTypes) {
                var columns = [];
                for (var i = 0; i < attributeDefinitions.length; i++) {
                    if (mapAccessLevel.isPublic && !attributeDefinitions[i].IsPublished) continue;

                    var column = { field: "Attributes." + attributeDefinitions[i].Id, name: attributeDefinitions[i].Id };
                    if (attributeTypes.isDateType(attributeDefinitions[i].Type)) {
                        angular.extend(column, { type: "date", dateFormat: "D MMM, YYYY", validator: factory.dateValidator, allowInvalid: false });
                    }
                    columns.push(column);
                }
                return columns;
            }
        }

        return factory;
    }
]);
