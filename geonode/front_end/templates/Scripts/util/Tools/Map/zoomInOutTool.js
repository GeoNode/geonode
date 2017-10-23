mapModule.factory('ZoomInOutTool', [
    function() {
        return function ZoomInOutTool(olView) {
            this.zoomIn = function() {
                olView.setZoom(olView.getZoom() + 1);
            };
            this.zoomOut = function() {
                olView.setZoom(olView.getZoom() - 1);
            };
        };
    }
]);