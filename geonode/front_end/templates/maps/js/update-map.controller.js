(function() {
    appModule
        .controller('MapUpdateController', MapUpdateController);

    MapUpdateController.$inject = ['mapService', '$window', 'analyticsService'];

    function MapUpdateController(mapService, $window, analyticsService) {
        var self = this;
        var map = mapService.getMap();
        self.MapConfig = $window.mapConfig;
        console.log(self.MapConfig);
        mapService.setMapName(self.MapConfig.about.title);
        self.MapConfig.map.layers.forEach(function(layer) {
            console.log(layer);
            var url = self.MapConfig.sources[layer.source].url;
            if (url) {
                layer.geoserverUrl = url;
                mapService.addDataLayer(_map(layer), false);
                // mapService.addVectorLayer(new ol.layer.Tile({
                //         extent: layer.bbox,
                //         source: new ol.source.TileWMS({
                //             url: url,
                //             params: { 'LAYERS': layer.name, 'TILED': true },
                //             serverType: 'geoserver'
                //         })
                //     }))
                // mapService.addVectorLayer(vector);
            }
        });

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
                "LayerId": _uuid(),
                "Name": layer.name,
                "SortOrder": order || 0,
                // "LastUpdateOn": "2017-10-10T11:10:26.083Z",
                "ClassifierDefinitions": {},
                "CanWrite": true,
                // "DataId": "s_facf34ee54914605943fe987f5b3637c",
                "ShapeType": "point",
                "Style": { /* not available */
                        "Name": _uuid(),
                        "default": {
                            "fillPattern": null,
                            "textFillColor": "#222026",
                            "text": null,
                            "pixelDensity": null,
                            "strokeDashstyle": "solid",
                            "strokeWidth": 1.0,
                            "strokeColor": "#5EF1F2",
                            "strokeOpacity": null,
                            "fillOpacity": 0.75,
                            "fillColor": "#2f7979",
                            "pointRadius": 14.0,
                            "graphicName": "circle",
                            "textGraphicName": null,
                            "externalGraphic": null,
                            'name': layer.name,
                            'userStyle': userStyle
                        },
                        "select": {
                            "fillPattern": "",
                            "textFillColor": "#222026",
                            "text": null,
                            "pixelDensity": null,
                            "strokeDashstyle": "solid",
                            "strokeWidth": 1.0,
                            "strokeColor": "#0000ff",
                            "strokeOpacity": 1.0,
                            "fillOpacity": 0.4,
                            "fillColor": "#0000ff",
                            "pointRadius": 6.0,
                            "graphicName": "circle",
                            "textGraphicName": null,
                            "externalGraphic": null,
                            'name': layer.name,
                            'userStyle': userStyle
                        },
                    "labelConfig": {
                        //         "attribute": null,
                        "visibilityZoomLevel": 0,
                        //         "font": "Times",
                        //         "fontStyle": "normal",
                        //         "fontWeight": "normal",
                        //         "color": "#000000",
                        //         "borderColor": "#ffffff",
                        //         "showBorder": true,
                        //         "size": 10.0,
                        //         "alignment": 1.0,
                        //         "offsetX": 0.0,
                        //         "offsetY": 0.0,
                        //         "rotation": 0.0,
                        //         "followLine": false,
                        //         "repeat": false,
                        //         "repeatInterval": 5.0,
                        //         "wrap": false,
                        //         "wrapPixel": 50.0
                    }
                },
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
                // "AttributeDefinition": [{ /* not available*/
                //     "Id": "s_985cd4386b6a4762812371ca8ae4c5a3",
                //     "Name": "category",
                //     "AttributeName": null,
                //     "IsPublished": true,
                //     "Type": "text",
                //     "Length": 30,
                //     "Precision": null,
                //     "Scale": null
                // }, {
                //     "Id": "s_5d1416d309df49cab55858ff2b463f70",
                //     "Name": "name",
                //     "AttributeName": null,
                //     "IsPublished": true,
                //     "Type": "text",
                //     "Length": 92,
                //     "Precision": null,
                //     "Scale": null
                // }],
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

        (function(){

            // map load
            //debugger
            map.on('postrender', function(evt){
                //console.log('maploaded', evt);
                var user_href = window.location.href.split('/');
                var map_info = user_href[user_href.length - 2];

                // Map load
                var user_location = JSON.parse(localStorage.getItem("user_location"));

                var url = '/analytics/api/map/load/create/';

                var latitude;
                var longitude;
                try{
                    latitude = user_location.latitude.toString();
                    longitude = user_location.longitude.toString()
                }catch(err){
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
            map.on('pointerdrag', function(evt){
                //console.log('pointerdrag', arguments);
                var user_location = JSON.parse(localStorage.getItem("user_location"));

                var url = '/analytics/api/user/activity/create/';

                var latitude;
                var longitude;
                try{
                    latitude = user_location.latitude.toString();
                    longitude = user_location.longitude.toString()
                }catch(err){
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
            map.getView().on('change:resolution', function(evt){

                var zoomType;
                var user_location = JSON.parse(localStorage.getItem("user_location"));

                var url = '/analytics/api/user/activity/create/';

                var latitude = '';
                var longitude = '';

                // Zoom in
                if(evt.oldValue > evt.currentTarget.getResolution()){
                    //console.log("Zoom in called");
                    zoomType = 'zoom-in'
                }

                // Zoom out
                if(evt.oldValue < evt.currentTarget.getResolution()){
                    //console.log("Zoom out called");
                    zoomType = 'zoom-out'
                }

                try{
                    latitude = user_location.latitude.toString();
                    longitude = user_location.longitude.toString()
                }catch(err){
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