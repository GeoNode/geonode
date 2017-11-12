(function() {
    angular
        .module('LayerApp')
        .controller('AttributeViewController', AttributeViewController);

    AttributeViewController.$inject = ['$location', 'LayerService', 'uiGridConstants'];

    function AttributeViewController($location, LayerService, uiGridConstants) {
        var self = this;
        self.geoServerUrl = '';
        self.propertyNames = [];
        // self.layerName = $location.search().name;
        self.layerName = $location.path().split('/').pop();
        self.gridOptions = {
            paginationPageSizes: [25, 50, 75, 100],
            paginationPageSize: 25,
            data: [],
            minRowsToShow: 15,
            enableHorizontalScrollbar : uiGridConstants.scrollbars.ALWAYS
        };
        
        function errorFn() {

        }

        function getFeatureDetails(url, layerName, propertyName) {
            LayerService.getFeatureDetails(url, layerName, propertyName).then(function(res) {
                self.attributeDetails = [];
                res.features.forEach(function(e) {
                    self.attributeDetails.push(e.properties);
                });
                self.gridOptions.data = self.attributeDetails;
                $('#attribute_view_left').hide();
            }, errorFn);
        }

        function getLayerFeature(url, layerName) {
            LayerService.getLayerFeatureByName(url, layerName).then(function(res) {
                res.featureTypes.forEach(function(featureType) {
                    featureType.properties.forEach(function(e) {
                        if (e.name !== 'the_geom')
                            self.propertyNames.push(e.name);
                    }, this);
                }, this);
                getFeatureDetails(url, layerName, self.propertyNames);
            }, errorFn);

        }

        function getLayerByName() {
            LayerService.getLayerByName(self.layerName)
                .then(function(res) {
                    getLayerFeature(self.geoServerUrl, res.typename);
                }, errorFn);
        }

        function getGeoServerSettings() {
            LayerService.getGeoServerSettings()
                .then(function(res) {
                    self.geoServerUrl = res.url;
                    getLayerByName();

                }, errorFn);
        }

        // Initialize Call
        (getGeoServerSettings)();
    }
})();