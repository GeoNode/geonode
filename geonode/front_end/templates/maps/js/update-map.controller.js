(function() {
    appModule
        .controller('MapUpdateController', MapUpdateController);

    MapUpdateController.$inject = ['mapService', '$window', 'analyticsService', 'LayerService', '$scope'];

    function MapUpdateController(mapService, $window, analyticsService, LayerService, $scope) {
        var self = this;
        var map = mapService.getMap();
        self.MapConfig = $window.mapConfig;

        mapService.setMapName(self.MapConfig.about.title);

        function setLayers() {
            self.MapConfig.map.layers.forEach(function(layer) {
                console.log(layer);
                var url = self.MapConfig.sources[layer.source].url;
                if (url) {
                    layer.geoserverUrl = url;
                    getLayerFeature(self.geoServerUrl, layer);
                }
            });
        }

        function errorFn() {

        }

        function getGeoServerSettings() {
            self.propertyNames = [];
            LayerService.getGeoServerSettings()
                .then(function(res) {
                    self.geoServerUrl = res.url;
                    setLayers();
                }, errorFn);
        }

        $scope.$on('layerPropertiesChanged', function(event, args) {
            var mapId = self.MapConfig.id;
            var style = args.layer.getStyle();
            args.layer.ClassifierDefinitions = style.classifierDefinitions || {};
            mapService.updateMapLayer(mapId, args.layer.Name, {
                styles: style.id
            });
        });

        function _setStyle(layer, new_layer) {
            new_layer.ClassifierDefinitions = new_layer.Style.classifierDefinitions || {};
            mapService.addDataLayer(new_layer, false);
        }

        function getStyle(styleId, layer, new_layer) {
            LayerService.getStyle(styleId)
                .then(function(res) {
                    new_layer.Style = res;
                    _setStyle(layer, new_layer);

                }, function() {
                    new_layer.Style = LayerService.getNewStyle();
                    _setStyle(layer, new_layer);
                });
        }

        function getLayerStyle(layer, new_layer) {
            LayerService.getLayerByMap(self.MapConfig.id, layer.name)
                .then(function(res) {
                    getStyle(res.styles, layer, new_layer);
                }, errorFn);
        }

        function getLayerFeature(url, layer) {
            LayerService.getLayerFeatureByName(url, layer.name).then(function(res) {
                res.featureTypes.forEach(function(featureType) {
                    var new_layer = _map(layer);
                    new_layer.AttributeDefinition = [];
                    featureType.properties.forEach(function(e) {
                        if (e.name === 'the_geom') {
                            if (e.localType.toLowerCase().search('polygon') != -1)
                                new_layer["ShapeType"] = 'polygon';
                            else if (e.localType.toLowerCase().search('point') != -1)
                                new_layer["ShapeType"] = 'point';
                        } else {
                            new_layer.AttributeDefinition.push({
                                "Id": e.name,
                                "Name": e.name,
                                "AttributeName": null,
                                "IsPublished": true,
                                "Type": e.localType,
                                "Length": 92,
                                "Precision": null,
                                "Scale": null
                            });
                        }
                    }, this);
                    getLayerStyle(layer, new_layer);
                }, this);
            }, errorFn);
        }

        function _uuid() {
            function _() {
                var rand = Math.ceil(1e15 + Math.random() * 1e5).toString(16);
                return rand.substring(rand.length - 4);
            }
            return _() + _() + '-' + _() + '-' + _() + '-' + _() + '-' + _() + _();
        }

        function _map(layer, order) {
            if (!layer.bbox) {
                layer.bbox = [-9818543.41779904, 5183814.6260749, -9770487.95134629, 5235883.07751104];
            }
            var userStyle = layer.name + '_' + _uuid();
            return {
                "LayerId": layer.name,
                "Name": layer.name,
                "SortOrder": order || 0,
                // "LastUpdateOn": "2017-10-10T11:10:26.083Z",
                "ClassifierDefinitions": {},
                "CanWrite": true,
                // "DataId": "s_facf34ee54914605943fe987f5b3637c",
                // "ShapeType": "point",

                "VisualizationSettings": null,
                "IsVisible": layer.visibility,
                "Filters": [],
                "ZoomLevel": 0,
                "ModificationState": "Added",
                "LayerExtent": {
                    "MinX": layer.bbox[0],
                    "MinY": layer.bbox[1],
                    "MaxX": layer.bbox[3],
                    "MaxY": layer.bbox[2]
                },
                "AttributeDefinition": [{ /* not available*/
                        "Id": "NAME_3",
                        "Name": "NAME_3",
                        "AttributeName": null,
                        "IsPublished": true,
                        "Type": "text",
                        "Length": 30,
                        "Precision": null,
                        "Scale": null
                    }, {
                        "Id": "NAME_2",
                        "Name": "NAME_2",
                        "AttributeName": null,
                        "IsPublished": true,
                        "Type": "text",
                        "Length": 92,
                        "Precision": null,
                        "Scale": null
                    },
                    {
                        "Id": "NAME_4",
                        "Name": "NAME_4",
                        "AttributeName": null,
                        "IsPublished": true,
                        "Type": "text",
                        "Length": 92,
                        "Precision": null,
                        "Scale": null
                    }
                ],
                // "IdColumn": "gid",
                "LinearUnit": "Meter",
                "IsLocked": false,
                "DataSourceName": "illinois_poi",
                "SourceFileExists": true,
                "IsDataOwner": true,
                "IsRaster": false,
                "geoserverUrl": layer.geoserverUrl,
                // "SavedDataId": "s_fe297a3305394811919f33cdb16fc30d"
            };
        }
        
        (getGeoServerSettings)();

        (function() {

            // map load
            //debugger
            map.on('postrender', function(evt) {
                //console.log('maploaded', evt);
                var user_href = window.location.href.split('/');
                var map_info = user_href[user_href.length - 2];

                // Map load
                var user_location = JSON.parse(localStorage.getItem("user_location"));

                var url = '/analytics/api/map/load/create/';

                var latitude;
                var longitude;
                try {
                    latitude = user_location.latitude.toString();
                    longitude = user_location.longitude.toString()
                } catch (err) {
                    latitude = "";
                    longitude = "";
                }

                var data = {
                    'user': user_info,
                    'map': map_info,
                    'latitude': latitude,
                    'longitude': longitude,
                    'agent': '',
                    'ip': ''
                };

                analyticsService.saveAnalytics(data, url);
            });

            // Map drag / pan event
            map.on('pointerdrag', function(evt) {
                //console.log('pointerdrag', arguments);
                var user_location = JSON.parse(localStorage.getItem("user_location"));

                var url = '/analytics/api/user/activity/create/';

                var latitude;
                var longitude;
                try {
                    latitude = user_location.latitude.toString();
                    longitude = user_location.longitude.toString()
                } catch (err) {
                    latitude = "";
                    longitude = "";
                }

                var user_href = window.location.href.split('/');
                var map_info = user_href[user_href.length - 2];

                var data = {
                    'user': user_info,
                    'layer': layer_info,
                    'map': map_info,
                    'activity_type': 'pan',
                    'latitude': latitude,
                    'longitude': longitude,
                    'agent': '',
                    'ip': '',
                    'point': ''
                };

                analyticsService.saveAnalytics(data, url);

            });

            //zoom in out event
            map.getView().on('change:resolution', function(evt) {

                var zoomType;
                var user_location = JSON.parse(localStorage.getItem("user_location"));

                var url = '/analytics/api/user/activity/create/';

                var latitude = '';
                var longitude = '';

                // Zoom in
                if (evt.oldValue > evt.currentTarget.getResolution()) {
                    //console.log("Zoom in called");
                    zoomType = 'zoom-in'
                }

                // Zoom out
                if (evt.oldValue < evt.currentTarget.getResolution()) {
                    //console.log("Zoom out called");
                    zoomType = 'zoom-out'
                }

                try {
                    latitude = user_location.latitude.toString();
                    longitude = user_location.longitude.toString()
                } catch (err) {
                    latitude = "";
                    longitude = "";
                }

                var user_href = window.location.href.split('/');
                var map_info = user_href[user_href.length - 2];

                var data = {
                    'user': user_info,
                    'layer': layer_info,
                    'map': map_info,
                    'activity_type': zoomType,
                    'latitude': latitude,
                    'longitude': longitude,
                    'agent': '',
                    'ip': '',
                    'point': ''
                };

                analyticsService.saveAnalytics(data, url);

            });



        })();
    }

})();