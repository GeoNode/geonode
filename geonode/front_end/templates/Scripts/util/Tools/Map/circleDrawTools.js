mapModule
    .factory('CircleDrawTool', CircleDrawTool);

CircleDrawTool.$inject = ['mapService'];

function CircleDrawTool(mapService) {
    return function(map) {
        var _featureId = 'bounding-circle';
        var dragCursor = 'pointer';
        var dragPrevCursor, dragCoordinate;
        var draggableFeature;
        var resizeFeaturePoint;
        var resizeFeature;
        var map = map || mapService.getMap();

        var STROKE_WIDTH = 3,
        CIRCLE_RADIUS = 5;

    var FILL_COLOR = 'rgba(255, 255, 255, 0.5)',
        STROKE_COLOR = 'rgba(0, 60, 136, 0.8)'; 

    var verticeStyle = new ol.style.Style({
        image: new ol.style.Circle({
            radius: CIRCLE_RADIUS,
            stroke: new ol.style.Stroke({
                color: STROKE_COLOR,
                width: STROKE_WIDTH
            }),
            fill: new ol.style.Fill({
                color: FILL_COLOR
            })
        })
    });

        var features = new ol.Collection();
        features.on('add', function(event) {
            var feature = event.element;
            feature.set('id', _featureId);
        });
        var vectorSource = new ol.source.Vector({
            features: features
        });
        var layer = new ol.layer.Vector({
            source: vectorSource
        });

        mapService.addVectorLayer(layer);

        function _getFeatureFromPixel(pixel) {
            var feature = map.forEachFeatureAtPixel(pixel, function(feature, layer) {
                
                return feature;
            });
            return feature;
        }
        dragInteraction = new ol.interaction.Pointer({
            handleDownEvent: function(event) {
                var feature = _getFeatureFromPixel(event.pixel);

                if (feature && feature.get('id') === _featureId) {
                    dragCoordinate = event.coordinate;

                    // draggableFeature = feature;
                    parentFeature = feature.get('parentFeature');
                    if (parentFeature) {
                        resizeFeature = feature;
                        draggableFeature = parentFeature;
                    } else {
                        draggableFeature = feature;
                    }
                    return true;
                }
                return false;
            },
            handleDragEvent: function(event) {
                var deltaX = event.coordinate[0] - dragCoordinate[0];
                var deltaY = event.coordinate[1] - dragCoordinate[1];
                draggableFeature.getGeometry().translate(deltaX, deltaY);
                if(resizeFeature)
                    resizeFeature.getGeometry().translate(deltaX, deltaY);
                dragCoordinate = event.coordinate;
            },  
            handleMoveEvent: function(event) {
                if (dragCursor) {
                    var map = event.map;
                    var feature = _getFeatureFromPixel(event.pixel);
                    var element = map.getTargetElement();
                    if (feature && feature.get('id') == _featureId) {
                        if (element.style.cursor != dragCursor) {
                            dragPrevCursor = element.style.cursor;
                            element.style.cursor = dragCursor;
                        }
                    } else if (dragPrevCursor != undefined) {
                        element.style.cursor = dragPrevCursor;
                        dragPrevCursor = undefined;
                    }

                }
            },
            handleUpEvent: function(event) {

            }
        });
        drawInteraction = new ol.interaction.Draw({
            source: vectorSource,
            type: 'Circle'
        });

        drawInteraction.on('drawend', function(event) {
            mapService.addInteraction(dragInteraction);
            mapService.removeInteraction(drawInteraction);
            var geometry = event.feature.getGeometry();
            var centerCoordinate = geometry.getCenter();
            var radious = geometry.getRadius();
            resizeFeaturePoint = new ol.Feature({
                geometry: new ol.geom.Point([centerCoordinate[0] + radious, centerCoordinate[1]]),
                name: 'resizeFeaturePoint',
                parentFeature: event.feature,
                // updateFn: updateBottomRight
            });

            resizeFeaturePoint.setStyle(verticeStyle);
            vectorSource.addFeature(resizeFeaturePoint);
            
        });

        this.Draw = function() {
            mapService.addInteraction(drawInteraction);
        };
    };
}