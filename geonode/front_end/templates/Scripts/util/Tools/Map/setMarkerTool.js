mapModule
    .factory('SetMarkerTool', SetMarkerTool);
SetMarkerTool.$inject = ['mapService', 'layerService'];

function SetMarkerTool(mapService, layerService) {
    return function SetMarkerTool(map, view) {
        var container, content, close, popup;
        this.showPopup = false;

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
                name: 'Lat: ' + latLong[1] + ' lon: ' + latLong[0],
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
                info_format: 'application/json',
                exceptions: 'application/json',
                x: Math.round(event.pixel[0]),
                y: Math.round(event.pixel[1])
            };
            container.style.visibility = 'visible';
            layerService.fetchWMSFeatures(urlParams)
                .then(function(res) {
                    var html = feature.get('name');
                    var properties = res.features.length > 0 ? res.features[0].properties : {};
                    for (var key in properties) {
                        html += "<p>" + key + ": " + res.features["0"].properties[key] + "</p>";
                    }
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
    };
}