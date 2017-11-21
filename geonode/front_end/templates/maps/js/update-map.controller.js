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

                map.addLayer(new ol.layer.Tile({
                        extent: layer.bbox,
                        source: new ol.source.TileWMS({
                            url: url,
                            params: { 'LAYERS': layer.name, 'TILED': true },
                            serverType: 'geoserver'
                        })
                    }))
                    // mapService.addVectorLayer(vector);
            }
        });
    }

})();