(function() {
    appModule
        .controller('MapUpdateController', MapUpdateController);

    MapUpdateController.$inject = ['mapService', '$window'];

    function MapUpdateController(mapService, $window) {
        var self = this;
        var map = mapService.getMap();
        self.MapConfig = $window.mapConfig;
        console.log(self.MapConfig);
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

        function _map(layer, order){
            if(!layer.bbox){
                layer.bbox =  [-9818543.41779904,  5183814.6260749, -9770487.95134629,  5235883.07751104];                
            }
            return {
                "LayerId": "s_31b086d815f5492a9da932bbf9af7333",
                "Name": layer.name,
                "SortOrder": order || 0,
                // "LastUpdateOn": "2017-10-10T11:10:26.083Z",
                "ClassifierDefinitions": {},
                "CanWrite": true,
                // "DataId": "s_facf34ee54914605943fe987f5b3637c",
                "ShapeType": "point",
                 "Style": { /* not available */
                //     "Name": "s_a5170c56d2a64a0c8ee7dff53d916e71",
                //     "default": {
                //         "fillPattern": null,
                //         "textFillColor": "#222026",
                //         "text": null,
                //         "pixelDensity": null,
                //         "strokeDashstyle": "solid",
                //         "strokeWidth": 1.0,
                //         "strokeColor": "#5EF1F2",
                //         "strokeOpacity": null,
                //         "fillOpacity": 0.75,
                //         "fillColor": "#2f7979",
                //         "pointRadius": 14.0,
                //         "graphicName": "circle",
                //         "textGraphicName": null,
                //         "externalGraphic": null
                //     },
                //     "select": {
                //         "fillPattern": "",
                //         "textFillColor": "#222026",
                //         "text": null,
                //         "pixelDensity": null,
                //         "strokeDashstyle": "solid",
                //         "strokeWidth": 1.0,
                //         "strokeColor": "#0000ff",
                //         "strokeOpacity": 1.0,
                //         "fillOpacity": 0.4,
                //         "fillColor": "#0000ff",
                //         "pointRadius": 6.0,
                //         "graphicName": "circle",
                //         "textGraphicName": null,
                //         "externalGraphic": null
                //     },
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
    }

})();