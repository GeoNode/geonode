mapModule.factory('featureService', [
    'featureRepository', '$rootScope', 'layerRepository', '$timeout', 'attributeTypes', '$q', 'surfFeatureFactory',
    function (featureRepository, $rootScope, layerRepository, $timeout, attributeTypes, $q, surfFeatureFactory) {
        var _activeFeature = undefined;
        var _attributeEditable = false;

        var factory = {
            createFeature: function (surfFeature, skipValidation) {
                if (!skipValidation && !surfFeature.isValid()) {
                    var deferred = $q.defer();
                    deferred.reject('invalid geometry');
                    return deferred.promise;
                }
                var params = postParams(surfFeature);
                params.attributes = surfFeature.getAttributesWithType() || [];
                return featureRepository.createFeature(params).success(function (result) {
                    surfFeature.setFid(result.FId);
                    layerRepository.updateLayerExtent(surfFeature.layer);
                    surfFeatureFactory.upsertToCache(surfFeature.layer, surfFeature.getFid(), surfFeature.olFeature);
                });
            },
            deleteFeature: function (surfFeature) {
                var fid = surfFeature.getFid();
                return factory.deleteFeatures([fid], surfFeature.layer);
            },
            deleteFeatures: function(deletedFids, surfLayer) {
                return featureRepository.deleteFeatures(deletedFids, surfLayer.LayerId).success(function () {
                    for (var i in deletedFids) {
                        surfFeatureFactory.deleteFromCache(surfLayer, deletedFids[i]);
                    }
                    layerRepository.updateLayerExtent(surfLayer);
                    factory.updateClassifier(surfLayer);
                });
            },
            editFeature: function (surfFeature) {
                var params = postParams(surfFeature);
                return featureRepository.editFeature(params).success(function () {
                    layerRepository.updateLayerExtent(surfFeature.layer);
                    surfFeatureFactory.upsertToCache(surfFeature.layer, surfFeature.getFid(), surfFeature.olFeature);
                });
            },
            hasActive: function () {
                return !!_activeFeature;
            },
            setActive: function (newActive) {
                if (newActive != _activeFeature) {

                    _attributeEditable = false;

                    var oldActive = _activeFeature;
                    $timeout(function () {
                        $rootScope.$apply(function () {
                            _activeFeature = newActive;
                        });
                    });

                    if (oldActive && !oldActive.layer.isRemoved()) {
                        factory.saveAttributes([oldActive]);
                        $('#ui-datepicker-div').hide();
                    }
                }
            },
            getActive: function () {
                return _activeFeature;
            },
            removeImageFromActiveFeature: function (image) {
                var layerId = _activeFeature.layer.getId();
                var fid = _activeFeature.getFid();
                _activeFeature.removeImage(image);
                return featureRepository.removeImage(layerId, fid, image.id);
            },
            saveAttributes: function (surfFeatures, saveAlways) {

                if (surfFeatures.length == 0) return;
                var attributesChanged;

                var surfLayer = surfFeatures[0].layer;

                var editedAttributes = [];
                for (var featureIndex in surfFeatures) {
                    var surfFeature = surfFeatures[featureIndex];

                    if (surfFeature.isAttributesChanged() || saveAlways) {
                        attributesChanged = true;
                        surfFeature.updateAttributes();
                        editedAttributes.push({
                            attributes: surfFeature.getAttributesWithType(),
                            fid: surfFeature.getFid()
                        });
                    }
                }
                if (attributesChanged) {
                    featureRepository.saveAttributes(surfLayer.getId(), editedAttributes).success(function () {
                        if (surfLayer.hasClassifierDefinitions() || surfLayer.hasLabeling()) {
                            surfLayer.refresh();
                            if (surfLayer.hasClassifierDefinitions()) {
                                factory.updateClassifier(surfLayer);
                            }
                        }
                    });
                }
            },
            updateClassifier: function (surfLayer) {
                if (!surfLayer.hasClassifierDefinitions()) return;
                factory.updateClassCounts(surfLayer).success(function () {
                    var classifierDefinition = surfLayer.getClassifierDefinitions();
                    var validClasses = [];
                    for (var i in classifierDefinition.selected) {
                        if (classifierDefinition.selected[i]) {
                            if (classifierDefinition.selected[i].count) {
                                validClasses.push(classifierDefinition.selected[i]);
                            }
                        }
                    }
                    classifierDefinition.selected = validClasses;
                    layerRepository.saveClassifierDefinitions(surfLayer.getId(), classifierDefinition);
                });
            },
            updateClassCounts: function (surfLayer) {
                var classifierDefinition = surfLayer.getClassifierDefinitions();

                if (classifierDefinition.isRange == 'true') {
                    return layerRepository.getRangeClassesWithCount(surfLayer.getId(), classifierDefinition.selectedField, classifierDefinition.selected)
                        .success(function (ranges) {
                            for (var i in classifierDefinition.selected) {
                                var item = _.findWhere(ranges, { rangeMin: classifierDefinition.selected[i].rangeMin, rangeMax: classifierDefinition.selected[i].rangeMax });
                                classifierDefinition.selected[i].count = item ? item.count : 0;
                            }
                        });
                } else {
                    return layerRepository.getUniqueClassesWithCount(surfLayer.getId(), classifierDefinition.selectedField)
                       .success(function (classesWithCount) {
                           for (var i in classifierDefinition.selected) {
                               var item = _.findWhere(classesWithCount, { value: classifierDefinition.selected[i].value });
                               classifierDefinition.selected[i].count = item ? item.count : 0;
                           }
                       });
                }
            },
            addRedoState: function (state) {
                var activeFeature = factory.getActive();
                if (activeFeature) {
                    activeFeature.redoList.push(state);
                }
            },
            getRedoState: function () {
                var activeFeature = factory.getActive();
                if (activeFeature) {
                    return activeFeature.redoList.pop();
                }
                return {};
            },
            addUndoState: function (state) {
                var activeFeature = factory.getActive();
                if (activeFeature) {
                    activeFeature.undoList.push(state);
                }
            },
            getUndoState: function () {
                var activeFeature = factory.getActive();
                if (activeFeature) {
                    return activeFeature.undoList.pop();
                }
                return {};
            },
            hasUndoState: function () {
                var activeFeature = factory.getActive();
                if (activeFeature) {
                    return activeFeature.undoList.length > 0;
                }
                return false;
            },
            hasRedoState: function () {
                var activeFeature = factory.getActive();
                if (activeFeature) {
                    return activeFeature.redoList.length > 0;
                }
                return false;
            },
            isAttributeEditable: function () {
                return _attributeEditable;
            },
            setAttributeEditableState: function (state) {
                _attributeEditable = state;
            }
        };

        function postParams(surfFeature) {
            var params = {
                LayerId: surfFeature.layer.getId(),
                FId: surfFeature.getFid(),
            }
            params.Wkt = surfFeature.getWkt();
            return params;
        }

        return factory;
    }]);