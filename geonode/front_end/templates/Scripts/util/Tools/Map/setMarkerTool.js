mapModule
    .factory('SetMarkerTool', SetMarkerTool);
SetMarkerTool.$inject = ['mapService', 'layerService', 'SettingsService'];

function SetMarkerTool(mapService, layerService, SettingsService) {
    return function SetMarkerTool(map, view) {
        var container, content, close, popup;
        this.showPopup = false;
        this.elevationLayerName = "";

        function createPopup() {
            container = document.getElementById('popup');
            content = document.getElementById('popup-content');
            closer = document.getElementById('popup-closer');
            popup = new ol.Overlay({
                element: container,
                positioning: 'top-left',
                stopEvent: true,
                offset: [0, -48],
                autoPan: true,
                autoPanAnimation: {
                    duration: 250
                }
            });
            // map.addOverlay(popup);
            /**
             * Add a click handler to hide the popup.
             * @return {boolean} Don't follow the href.
             */
            closer.onclick = function(e) {
                popup.setPosition(undefined);
                closer.blur();
                return false;
            };
            // popup.setPosition(evt.coordinate);
            map.addOverlay(popup);

        }

        function addMarker(evt) {
            // var latLong = ol.proj.transform(evt.coordinate, 'EPSG:4326','EPSG:3857');
            var latLong = ol.proj.transform(evt.coordinate, 'EPSG:3857', 'EPSG:4326');
            var iconFeature = new ol.Feature({
                geometry: new ol.geom.Point(evt.coordinate),
                lat: latLong[1].toFixed(6),
                lon: latLong[0].toFixed(6),
                coordinate: evt.coordinate,
                population: 4000,
                rainfall: 500
            });

            var iconStyle = new ol.style.Style({
                image: new ol.style.Icon( /** @type {olx.style.IconOptions} */ ({
                    anchor: [0.5, 48],
                    anchorXUnits: 'fraction',
                    anchorYUnits: 'pixels',
                    opacity: 1,
                    // size: [120, 120],
                    src: '/static/geonode/img/marker.png'
                }))
            });

            iconFeature.setStyle(iconStyle);

            var vectorSource = new ol.source.Vector({
                features: [iconFeature]
            });

            var vectorLayer = new ol.layer.Vector({
                source: vectorSource
            });

            map.addLayer(vectorLayer);
            return iconFeature;
        }

        function showPopup(feature, event) {
            var size = map.getSize();
            var bbox = map.getView().calculateExtent(size);

            var urlParams = {
                bbox: bbox.join(','),
                width: size[0],
                height: size[1],
                query_layers: this.elevationLayerName,
                layers: this.elevationLayerName,
                info_format: 'application/json',
                exceptions: 'application/json',
                x: Math.round(event.pixel[0]),
                y: Math.round(event.pixel[1])
            };
            container.style.visibility = 'visible';
            layerService.fetchWMSFeatures(urlParams)
                .then(function(res) {
                    var lat = feature.get('lat');
                    var lon = feature.get('lon');
                    var html = "<div class='pop-up'> " +
                        "<p>Lat: " + lat + "</p>" +
                        "<p>Lon: " + lon + "</p>";
                    var properties = res.features.length > 0 ? res.features[0].properties : {};
                    for (var key in properties) {
                        html += "<p>Elevation: " + res.features["0"].properties[key] + "</p>";
                    }
                    html += "</div>";
                    content.innerHTML = html;
                }, function(error) {

                });
            content.innerHTML = feature.get('name');
            popup.setPosition(feature.get('coordinate'));
        }
        this.setMarker = function() {
            mapService.removeUserInteractions();
            mapService.removeEvents();
            createPopup();

            mapService.registerEvent('singleclick', function(evt) {
                var feature = map.forEachFeatureAtPixel(evt.pixel,
                    function(feature, layer) {
                        return feature;
                    });
                if (!feature) {
                    feature = addMarker(evt);
                }
                showPopup(feature, evt);
            });

        };

        function getSettings(){
            SettingsService.getSystemSettings()
            .then(function(res){
                var elevation = res.find(function(e){
                    return e.settings_code === 'elevation';
                });
                this.elevationLayerName = elevation && elevation.content_object.typename;
            });
        }

        function init(){
            getSettings();
        }

        (init)();
    };
}