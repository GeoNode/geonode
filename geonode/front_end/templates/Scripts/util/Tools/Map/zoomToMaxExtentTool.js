mapModule
    .factory('ZoomToMaxExtentTool', ZoomToMaxExtentTool);
ZoomToMaxExtentTool.$inject = ['$interval'];

function ZoomToMaxExtentTool($interval) {
    return function ZoomToMaxExtentTool(olView) {
        this.zoomToMaxExtent = function() {
            // let zoom = olView.getZoom();
            // $interval(function() {
            //     zoom--;
            //     olView.setZoom(zoom);
            // }, 100, zoom);
            olView.setZoom(olView.minZoom_);
        };
        this.canZoomToMaxExtent = function() {
            return olView.getZoom() == olView.minZoom_;
        };
    };
}