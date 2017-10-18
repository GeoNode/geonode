(function() {
    angular
        .module('LayerApp')
        .controller('AttributeViewController', AttributeViewController);
    AttributeViewController.$inject = ['$location', 'LayerService'];

    function AttributeViewController($location, LayerService) {
        var self = this;
        self.layerName = $location.search().name;

        function getFeatureDetails(url, layerName, propertyName) {
            LayerService.getFeatureDetails(url, layerName, propertyName).then(function(res) {
                self.attributeDetails = res.data;
                console.log(self.attributeDetails);
            }, function(error) {

            });
        }

        function getLayerFeature(url, layerName) {

            LayerService.getLayerFeatureByName(url, layerName).then(function(res) {
                console.log(res);
                self.propertyNames = [];
                res.data.featureTypes["0"].properties.forEach(function(e) {
                    if (e.name !== 'the_geom')
                        self.propertyNames.push(e.name);
                }, this);
                console.log(self.propertyNames);
                getFeatureDetails(url, layerName, self.propertyNames);
            }, function(error) {

            });

        }
        LayerService.getLayerByName(self.layerName)
            .then(function(res) {
                console.log(res);
                getLayerFeature(res.data.ows_url, res.data.typename);
            }, function(error) {

            });




    }
})();