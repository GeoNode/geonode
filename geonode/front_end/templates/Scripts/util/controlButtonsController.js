appModule.controller("controlButtonsController", ["$scope", "$modal", "$timeout", "$rootScope", "$window", "projectService", 'mapModes', 'mapService', 'dirtyManager', 'featureService', 'interactionHandler', 'mapTools', 'CircleDrawTool', 'LayerService',
    function($scope, $modal, $timeout, $rootScope, $window, projectService, mapModes, mapService, dirtyManager, featureService, interactionHandler, mapTools, CircleDrawTool, LayerService) {
        $scope.mapService = mapService;
        $scope.mapTools = mapTools;

        (function() {
            $scope.enable = {};

            $scope.enable.saveProject = function() {
                return dirtyManager.isDirty() | true;
            };
        })();

        (function() {
            $scope.action = {};

            $rootScope.action = $rootScope.action || {};
            $rootScope.action.saveProject = function() {
                var projectName = mapService.getMapName();
                if (projectName) {
                    mapService.saveMapAs(projectName).success(function(data) {
                        projectService.executeAfterSuccessfulSave(data.layerIdToSavedDataIdMappings);
                    });
                } else {
                    showProjectBrowserDialog(true);
                }
            };

            $scope.action.saveProject = $rootScope.action.saveProject;

            $scope.action.showCloseProjectOptions = function() {

                if (dirtyManager.isDirty()) {
                    dialogBox.multiAction({
                        text: appMessages.confirm.saveChanges,
                        width: '280px',
                        actions: {
                            "Save": function() {
                                projectService.setAfterSave(function() {
                                    mapService.closeWorkingMap();
                                    featureService.setActive(null);
                                });
                                $rootScope.action.saveProject();
                                interactionHandler.setMode(mapModes.select);
                            },
                            "Discard": function() {
                                mapService.closeWorkingMap();
                                dirtyManager.setDirty(false);
                            }
                        }
                    });
                } else {
                    mapService.closeWorkingMap();
                }
            };

            $scope.action.browseProject = function() {
                showProjectBrowserDialog(false);
            };

            $scope.action.overpassApiQuery = function() {
                showOverpassApiQueryDialog();
            };

            $scope.action.browseData = function() {
                $modal.open({
                    templateUrl: '/static/Templates/CatalogBrowser/Browser.html',
                    controller: 'catalogBrowserController',
                    backdrop: 'static',
                    keyboard: false,
                    windowClass: 'fullScreenModal'
                });
            };

            $scope.action.openHelp = function(url) {
                $window.open(url);
            };

            var transform, mapStyleElem, layerSwitcher, zoomControl;

            function moveShape() {
                mapStyleElem = $(".gm-style>div:first>div");
                if (!mapStyleElem || mapStyleElem.length == 0) return;
                transform = mapStyleElem.css("transform");
                var comp = transform.split(","); //split up the transform matrix
                var mapleft = parseFloat(comp[4]); //get left value
                var maptop = parseFloat(comp[5]); //get top value
                mapStyleElem.css({
                    "transform": "none",
                    "left": mapleft,
                    "top": maptop,
                });
            }

            function removeLayerSwitcher() {
                layerSwitcher = $(document.querySelector('.olControlLayerSwitcher.olControlNoSelect'));
                layerSwitcher.hide();
            }

            function removeZoomControl() {
                zoomControl = $(document.querySelector('.olControlZoom.olControlNoSelect'));
                zoomControl.hide();
            }

            function addLayerSwitcher() {
                layerSwitcher.show();
            }

            function addZoomControl() {
                zoomControl.show();
            }

            function restoreShape() {
                if (mapStyleElem && mapStyleElem.length > 0) {
                    $(".gm-style>div:first>div").css({
                        left: 0,
                        top: 0,
                        "transform": transform
                    });
                }
            }

            var visualizationLegendBottom;
            var classesToBeHide = ['.visulization-legend-container .donot-print', '.zoom-level-display',
                '.feature-edit-button-container', '.map-loading-icon', '.base-map-switcher'
            ];

            function styleContents() {
                visualizationLegendBottom = $('.visulization-legend-container').css('bottom');
                $('.visulization-legend-container').css('bottom', 20);
                classesToBeHide.forEach(function(item) {
                    $(item).hide();
                });
            }

            function restoreStyles() {
                $('.visulization-legend-container').css('bottom', visualizationLegendBottom);
                $('.visulization-legend-container').css('bottom', 20);
                classesToBeHide.forEach(function(item) {
                    $(item).show();
                });
            }
            var circle = new CircleDrawTool();
            $scope.action.drawCircle = function() {
                circle.Remove();
                circle.Draw();
                circle.OnModificationEnd(function(feature, values) {
                    var layers = mapService.getLayers();
                    for (var k in layers) {
                        var layer = layers[k];
                        LayerService.getWFS($window.GeoServerHttp2Root, {
                            _dc: 1510220556364,
                            version: '1.0.0',
                            request: 'GetFeature',
                            outputFormat: 'JSON',
                            srsName: 'EPSG:3857',
                            typeNames: layer.getName(),
                            cql_filter: 'DWithin(the_geom,POINT(' + values.center[1] + ' ' + values.center[0] + '),' + values.radius + ',meters)',
                        });
                    }
                });
            };

            $scope.action.printPreview = function() {

                $rootScope.mapImage = { baseMapUrl: undefined, shapeUrl: undefined };
                $modal.open({
                    templateUrl: './Print/PrintPreview',
                    controller: 'printPreviewController',
                    backdrop: 'static',
                    keyboard: false,
                    windowClass: 'fullScreenModal printPreviewModal'
                });

                moveShape();
                removeLayerSwitcher();
                removeZoomControl();
                styleContents();

                html2canvas($('#mainContent'), {
                    useCORS: true,
                    onrendered: function(canvas) {
                        restoreShape();
                        addLayerSwitcher();
                        addZoomControl();
                        restoreStyles();
                        $timeout(function() {
                            $rootScope.mapImage.baseMapUrl = canvas.toDataURL('image/png');
                        });
                    }
                });
            };
        })();

        $rootScope.selectedFeatureAttributes = [];

        function showProjectBrowserDialog(openForSave) {
            $modal.open({
                templateUrl: '/static/Templates/Project/Browser.html',
                controller: 'projectBrowserController',
                backdrop: 'static',
                keyboard: false,
                windowClass: 'fullScreenModal',
                resolve: {
                    showProjectNameInput: function() {
                        return openForSave || false;
                    }
                }
            });
        }

        function showOverpassApiQueryDialog() {
            $modal.open({
                templateUrl: '/static/Templates/Project/OverpassApiQueryBuilder.html',
                controller: 'OverpassApiQueryBuilderController',
                backdrop: 'static',
                keyboard: false,
                // windowClass: 'fullScreenModal'
            });
        }

        $scope.toggleMapEditable = function() {
            interactionHandler.toggleEditable();
        };
    }
]);