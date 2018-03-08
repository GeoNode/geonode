appModule.controller('attributeGridController', ['$scope', '$rootScope', 'featureRepository',
    'attributeGridService', 'attributeValidator', 'mapService', 'featureService', 'attributeTypes',
    'cqlFilterCharacterFormater', 'mapTools', '$timeout', 'mapAccessLevel', 'LayerService','surfToastr','urlResolver',
    function($scope, $rootScope, featureRepository, attributeGridService, attributeValidator,
        mapService, featureService, attributeTypes, cqlFilterCharacterFormater, mapTools, $timeout, mapAccessLevel, LayerService,surfToastr,urlResolver) {

        var surfLayer, activeLayerId;
        $scope.config = {};
        $scope.isQueryEnabled=false;
        $scope.query="";
        $scope.isBoundaryBoxEnabled=false;

        function getRequestObjectToGetFeature(featureID, typeName) {
            var requestObj = {
                request: 'GetFeature',
                typeName: typeName,
                maxFeatures: 1,
                featureID: featureID,
                version: '2.0.0',
                outputFormat: 'json',
                exceptions: 'application/json'
            };
            return requestObj;
        }
        
        $scope.selectedFeatures = [];
        var selectedFeatures = [];

        $scope.gridOptions = {
            enableSorting: true,
            enableColumnResizing: true,
            onRegisterApi: function(gridApi) {
                $scope.gridApi = gridApi;
                gridApi.selection.on.rowSelectionChanged($scope, function(rows) {
                    $scope.selectedFeatures = gridApi.selection.getSelectedRows();
                    var difference = _.difference($scope.selectedFeatures, selectedFeatures);
                    var features = _.map(difference, function(feature) {
                        return feature.Fid;
                    });
                    var featureId = features.join(",");
                    if (surfLayer) {
                        var requestObj = getRequestObjectToGetFeature(featureId, surfLayer.DataId);
                        LayerService.getWFSWithGeom('api/geoserver/', requestObj, false).then(function(response) {
                            attributeGridService.highlightFeature(response);
                            selectedFeatures=$scope.selectedFeatures;
                        });
                    }
                });
            },
            data: []
        };

        $scope.$watch(function() {
            return $rootScope.layerId;
        }, function() {
            if ($rootScope.layerId)
                initGrid($rootScope.layerId);
        });

        function initGrid(newActiveLayerId) {
            $scope.isQueryEnabled=false;
            $scope.query="";
            $scope.isBoundaryBoxEnabled=false;

            $scope.gridData = { attributeRows: [] };
            attributeGridService.resetAll();
            $scope.search = {};
            activeLayerId = newActiveLayerId;
            surfLayer = mapService.getLayer(activeLayerId);
            mapService.setAllFeaturesUnselected();
            //$scope.data = { loading: true, isReadonly: !surfLayer.isWritable() || !mapAccessLevel.isWritable };
            $scope.data = { loading: true, isReadonly: true };
            $scope.sorting = { predicate: null };
            $scope.pagination = { totalItems: 0, currentPage: 1, itemsPerPage: 10, pageSizes: [10, 50, 100] };
            $scope.gridData = { attributeDefinitions: [], attributeRows: [] };
            $scope.lastActiveHeader = { index: -1, isAccending: true };

            $scope.gridData.attributeDefinitions = surfLayer.getAttributeDefinition();
            $scope.gridApi = {};

            $scope.gridOptions = {
                enableSorting: true,
                enableColumnResizing: true,
                enableRowSelection: true,
                enableSelectAll: false,
                columnDefs: attributeGridService.getColumns($scope.gridData.attributeDefinitions, attributeTypes),
                onRegisterApi: function(gridApi) {
                    $scope.gridApi = gridApi;
                    gridApi.selection.on.rowSelectionChanged($scope, function(rows) {
                        $scope.selectedFeatures = gridApi.selection.getSelectedRows();
                        var difference = _.difference($scope.selectedFeatures, selectedFeatures);
                        var features = _.map(difference, function(feature) {
                            return feature.Fid;
                        });
                        var featureId = features.join(",");
                        if (surfLayer) {
                            var requestObj = getRequestObjectToGetFeature(featureId, surfLayer.DataId);
                            LayerService.getWFSWithGeom('api/geoserver/', requestObj, false).then(function(response) {
                                attributeGridService.highlightFeature(response);
                                selectedFeatures=$scope.selectedFeatures;
                            });
                        }
                    });
                },
                data: []
            };

            $scope.config = angular.extend($scope.config, {
                contextMenu: {
                    items: {
                        "remove_row": {
                            disabled: function() {
                                return $scope.data.isReadonly;
                            }
                        },
                        "alignment": {},
                        // "freeze_column": {} //todo: it sorts column, which creates problem with attribute definition mapping; need to figure this out later
                    }
                },
                manualColumnFreeze: true,
                stretchH: "all",
                // afterChange: function (change, source) {
                //     if (source === "edit") {
                //         attributeGridService.storeChanges(change, $scope.gridData.attributeRows);
                //     } else if (source === "autofill" || source === "paste") {
                //         attributeGridService.storeChanges(change, $scope.gridData.attributeRows);
                //     }
                // },
                // afterOnCellMouseDown: function (event, pos, elem) {
                //     if (pos.row === -1) {
                //         setActiveHeader(pos.col);
                //     }
                // },
                colHeaders: attributeGridService.getColumnHeaders($scope.gridData.attributeDefinitions),
                rowHeaders: true,
                columns: attributeGridService.getColumns($scope.gridData.attributeDefinitions, attributeTypes),
                manualColumnResize: true,
                manualRowResize: true,
                allowInsertRow: false,
                // afterCreateRow: function (index, amount) {
                //     $scope.gridData.attributeRows.splice(index, amount);
                // },
                // beforeRemoveRow: function (rowIndex) {
                //     attributeGridService.deleteRow($scope.gridData.attributeRows[rowIndex].Fid);
                // },
                // cells: function (row, col) {
                //     if (isNaN(col)) return { readOnly: $scope.data.isReadonly };
                //     return { readOnly: $scope.data.isReadonly || attributeTypes.isReadOnlyType($scope.gridData.attributeDefinitions[col].Type) }
                // },
                // beforeKeyDown: function (e) {
                //     validateAndUpdateValue(e);
                // }
            });

            loadAttributeGridInfo();
        }

        function validateAndUpdateValue(event) {
            var selectedCell = $scope.config.table.getSelected();
            if (selectedCell) {
                var valueBeforeChange = event.realTarget.value;
                $timeout(function() {
                    if (!isAttributeValid(event.realTarget.value, $scope.gridData.attributeDefinitions[selectedCell[1]])) {
                        event.realTarget.value = valueBeforeChange;
                    }
                });
            }
        }

        function stopLoading() {
            $scope.data.loading = false;
        }

        function loadAttributeGridInfo() {

            loadGridDataFromServer($scope.pagination.currentPage, stopLoading, stopLoading);
        }

        
        $rootScope.$on('filterDataWithCqlFilter', function(event, data) {
            $scope.pagination.currentPage = 1;
            $scope.query=data.query;
            $scope.isBoundaryBoxEnabled=data.bbox;
            if($scope.query){
                loadGridDataFromServerUsingCqlFilter($scope.pagination.currentPage, $scope.query,$scope.isBoundaryBoxEnabled);
                $scope.isQueryEnabled=true;
            }else{
                surfToastr.error("please enter a valid query","Error");
            }
        });

        function getRequestObject(currentPage) {
            var currentPageSize = $scope.pagination.itemsPerPage;
            var startIndex = currentPageSize * currentPage - currentPageSize;
            var requestObj = {
                request: 'GetFeature',
                typeName: surfLayer.DataId,
                startIndex: startIndex,
                count: currentPageSize,
                maxFeatures: currentPageSize,
                sortBy: $scope.sorting.predicate ? $scope.sorting.predicate + ($scope.lastActiveHeader.isAccending ? "" : "+D") : '', //surfLayer.IdColumn
                version: '1.0.0',
                outputFormat: 'GML2',
                exceptions: 'application/json'
            };

            if ($scope.search.attribute && $scope.search.value) {
                var searchValue = $scope.search.value;
                if (!attributeTypes.isNumericType($scope.search.attribute.Type)) {
                    requestObj.CQL_FILTER = $scope.search.attribute.Id + " ILIKE " + "'%25" + cqlFilterCharacterFormater.formatSpecialCharacters(searchValue) + "%25'";
                } else {
                    requestObj.CQL_FILTER = $scope.search.attribute.Id + "=" + searchValue;
                }
            }
            return requestObj;
        }

        function populateGrid(features, onSuccess) {
            attributeGridService.populateDataIntoGrid($scope.gridData, features);
            if (onSuccess) onSuccess();
            attributeGridService.changeEditedRows($scope.gridData);
            attributeGridService.removeDeletedRows($scope.gridData);
            $scope.loading = false;
            var settings = angular.extend({
                data: $scope.gridData.attributeRows
            }, $scope.config);
            $scope.gridOptions.data = $scope.gridData.attributeRows;
        }

        function loadGridDataFromServerUsingCqlFilter(currentPage, query,isBoundaryBoxEnabled, onSuccess, onError) {
            if($rootScope.layerId){
                $scope.loading = true;
                var requestObj = getRequestObject(currentPage);
                requestObj.CQL_FILTER = query;
                if(isBoundaryBoxEnabled){
                    requestObj.CQL_FILTER= requestObj.CQL_FILTER + ' AND BBOX(the_geom,' +mapService.getBbox('EPSG:4326')+')';
                }
                requestObj.outputFormat='json';
                LayerService.getWFS('api/geoserver/', requestObj,false).then(function(data){
                    populateGrid(data.features);
                    $scope.pagination.totalItems=data.totalFeatures;
                }).catch(function() {
                        if (onError) {
                            onError();
                        }
                        $scope.loading = false;
                    });

            }else{
                surfToastr.error("please select a layer","Error");
            }
            
        }

        function loadGridDataFromServer(currentPage, onSuccess, onError) {
            $scope.loading = true;
            if($scope.isQueryEnabled){
                loadGridDataFromServerUsingCqlFilter(currentPage,$scope.query,$scope.isBoundaryBoxEnabled);
            }else{
                var requestObj = getRequestObject(currentPage);
                requestObj.outputFormat='json';
                LayerService.getWFS('api/geoserver/', requestObj,false).then(function(data){
                    populateGrid(data.features);
                    $scope.pagination.totalItems=data.totalFeatures;
                }).catch(function() {
                    if (onError) {
                        onError();
                    }
                    $scope.loading = false;
                });
            }
        }

        $scope.searchByAttribute = function() {
            $scope.isBoundaryBoxEnabled=false;
            $scope.isQueryEnabled=false;
            loadGridDataFromServer($scope.pagination.currentPage);
            $scope.pagination.currentPage = 1;
        };

        $scope.onPageSelect = function(currentPage) {
            loadGridDataFromServer(currentPage);
            mapService.setAllFeaturesUnselected();
        };

        function setActiveHeader(colIndex) {
            if ($scope.lastActiveHeader.index === colIndex) {
                $scope.lastActiveHeader.isAccending = !$scope.lastActiveHeader.isAccending;
            } else {
                $scope.lastActiveHeader.index = colIndex;
                $scope.sorting.predicate = $scope.gridData.attributeDefinitions[colIndex].Id;
            }

            loadGridDataFromServer($scope.pagination.currentPage);
        }

        $scope.itemPerPageChanged = function() {
            $scope.pagination.currentPage = 1;
            loadGridDataFromServer($scope.pagination.currentPage);

            mapService.setAllFeaturesUnselected();
        };

        function isAttributeValid(item, attributeDefinition) {
            var isValid = true;
            if (attributeTypes.isNumericType(attributeDefinition.Type)) {
                isValid = attributeValidator.isNumberWithinRange(item, attributeDefinition.Precision, attributeDefinition.Scale);
            } else if (attributeTypes.isTextType(attributeDefinition.Type)) {
                isValid = attributeValidator.isTextLengthValid(item, attributeDefinition.Length);
            }
            return isValid;
        }


        function getMessageToShow() {
            return attributeGridService.hasSingleFeatureToDelete() ?
                appMessages.confirm.deleteSignleItemFromAttributeGrid :
                appMessages.confirm.deleteMultipleItemFromAttributeGrid;
        }

        function closeModal() {
            try {
                $modalInstance.close();
            } catch (error) {}
            $scope.config.table.destroy();
        }

        function saveFeatures() {
            var features = attributeGridService.getFeaturesWithChangedAttributes(activeLayerId);
            featureService.saveAttributes(features, true);
            mapTools.activeLayer.getActiveLayer().tools.selectFeature.unselectAllFeatures();
            closeModal();
        }

        $scope.saveChanges = function() {
            if (attributeGridService.haveFeaturesToDelete()) {
                dialogBox.confirm({
                    text: getMessageToShow(),
                    action: function() {
                        attributeGridService.removeDeletedFeatures(activeLayerId);
                        saveFeatures();
                    },
                    width: "350px"
                });
            } else {
                saveFeatures();
            }
        };

        //mapTools.activeLayer.events.register('changed', function (newActiveLayer) {
        //    initGrid(newActiveLayer.getId());
        //});

        //jantrik.EventPool.register('FeatureDeleted', function (fid) {
        //    attributeGridService.deletedRow(_.findWhere($scope.gridData.attributeRows, { Fid: fid }), $scope.gridData);
        //});

        $scope.closeAttributeGrid = function() {
            closeModal();
            mapService.setAllFeaturesUnselected();
        };
    }
]);