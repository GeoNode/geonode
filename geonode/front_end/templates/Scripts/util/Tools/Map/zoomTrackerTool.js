mapModule.factory('ZoomTrackerTool', [
    'jantrik.Event',
    function (Event) {
        return function ZoomTrackerTool(olMap) {
            var _thisTool = this;

            this.zoom = null;
            this.events = new Event();

            function updateZoom() {
                _thisTool.zoom = olMap.getView().getZoom();
                _thisTool.events.broadcast('changed', _thisTool.zoom);
            }

            updateZoom();

            olMap.getView().on('change:resolution', updateZoom);
        };
    }
]);