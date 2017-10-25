mapModule
    .factory('SetMarkerTool', SetMarkerTool);
SetMarkerTool.$inject = [];

function SetMarkerTool($interval) {
    return function SetMarkerTool(map, view) {
        this.setMarker = function() {
            console.log('Marker Set');
        };
    };
}