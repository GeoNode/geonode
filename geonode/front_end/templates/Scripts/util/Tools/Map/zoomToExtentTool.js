mapModule
    .factory('ZoomToExtentTool', ZoomToExtentTool);
ZoomToExtentTool.$inject = ['mapService'];

function ZoomToExtentTool(mapService) {
    return function ZoomToExtentTool() {
        this.isActivated = false;
        var draw = new ol.interaction.DragBox({
            // condition: ol.events.condition.altKeyonly,
            style: new ol.style.Style({
                stroke: new ol.style.Stroke({
                    color: [0, 0, 255, 1]
                })
            })
        });
        draw.on('boxend', function() {
            var boundingBox = draw.getGeometry().getCoordinates()[0];
            let ext = ol.extent.boundingExtent([
                boundingBox[0],
                boundingBox[2]
            ]);
            mapService.zoomToExtent(ext);
        });
        this.drawBox = function() {
            //Dragbox - select
            if (!this.isActivated) {
                this.isActivated = true;
                mapService.addInteraction(draw);
            } else {
                this.isActivated = false;
                mapService.removeInteraction(draw);
            }

            //Dragbox - get coordinates to fields

        };
    };
}