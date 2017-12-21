(function() {
    appModule
        .controller('MapUpdateController', MapUpdateController);

    MapUpdateController.$inject = ['mapService', '$window', 'analyticsService', 'LayerService'];

    function MapUpdateController(mapService, $window, analyticsService, LayerService) {
        var self = this;
        var map = mapService.getMap();
        self.MapConfig = $window.mapConfig;
        console.log(self.MapConfig);
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
        function getDefaultStyle(){
            return { /* not available */
                "Name": _uuid(),
                "default": {
                    "fillPattern": null,
                    "textFillColor": "#0000ff",
                    "text": null,
                    "pixelDensity": null,
                    "strokeDashstyle": "solid",
                    "strokeWidth": 1.0,
                    "strokeColor": "#000000",
                    "strokeOpacity": null,
                    "fillOpacity": 0.75,
                    "fillColor": "#ffffff",
                    "pointRadius": 14.0,
                    "graphicName": "circle",
                    "textGraphicName": null,
                    "externalGraphic": null,
                },
                "select": {
                    "fillPattern": "",
                    "textFillColor": "#0000ff",
                    "text": null,
                    "pixelDensity": null,
                    "strokeDashstyle": "solid",
                    "strokeWidth": 1.0,
                    "strokeColor": "#000000",
                    "strokeOpacity": 1.0,
                    "fillOpacity": 0.4,
                    "fillColor": "#ff00ff",
                    "pointRadius": 6.0,
                    "graphicName": "circle",
                    "textGraphicName": null,
                    "externalGraphic": null,
                },
                "labelConfig": {
                    "attribute": null,
                    "visibilityZoomLevel": 0,
                    "font": "Times",
                    "fontStyle": "normal",
                    "fontWeight": "normal",
                    "color": "#000000",
                    "borderColor": "#ffffff",
                    "showBorder": true,
                    "size": 10.0,
                    "alignment": 1.0,
                    "offsetX": 0.0,
                    "offsetY": 0.0,
                    "rotation": 0.0,
                    "followLine": false,
                    "repeat": false,
                    "repeatInterval": 5.0,
                    "wrap": false,
                    "wrapPixel": 50.0
                },
                "classifierDefinitions": {}
            }
        }
        function getLayerStyle(layer, new_layer) {
            LayerService.getStyleByLayer(layer.name)
                .then(function(res) {
                    new_layer.Style = JSON.parse(res.style);
                    if(!new_layer.Style){
                        new_layer.Style = getDefaultStyle();
                    }
                    new_layer.Style.Name = res.name;
                    new_layer.Style.default.name = layer.name;
                    new_layer.Style.default.userStyle = res.name;
                    new_layer.Style.select.name = layer.name;
                    new_layer.Style.select.userStyle = res.name;
                    new_layer.ClassifierDefinitions = new_layer.Style.classifierDefinitions || {};
                    mapService.addDataLayer(new_layer, false);
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
                            
                            
                        }else {
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
                }],
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