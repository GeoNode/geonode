(function() {
    appModule
        .controller('MapController', MapController);

    MapController.$inject = ['mapService', '$window', 'analyticsService', 'LayerService', '$scope', 'layerService', 'queryOutputFactory', '$rootScope','$interval'];

    function MapController( mapService, $window, analyticsService, LayerService, $scope, oldLayerService, queryOutputFactory, $rootScope,$interval) {
        var self = this;
        var re = /\d*\/embed/;
        var map = mapService.getMap();
        self.MapConfig = $window.mapConfig;

        mapService.setMapName(self.MapConfig.about.title);
        mapService.setId(self.MapConfig.id);
        mapService.setMeta(self.MapConfig.about);

        function setLayers() {
            self.MapConfig.map.layers.forEach(function(layer) {
                var url = self.MapConfig.sources[layer.source].url;
                if (url) {
                    layer.geoserverUrl = re.test($window.location.pathname) ? getCqlFilterUrl(url) : url;
                    mapService.addDataLayer(oldLayerService.map(layer), false);
                }
            });
        }

        function errorFn() {

        }

        $scope.changeStyle = function(layerId, styleId) {
            var layer = mapService.getLayer(layerId);
            if (styleId) {
                LayerService.getStyle(styleId)
                    .then(function(res) {
                        layer.setStyle(res);
                        layer.refresh();
                    });
            } else {
                layer.setStyle(LayerService.getNewStyle());
                layer.refresh();
            }
        };

        $scope.group = { "a": "AND", "rules": [] };
        $scope.getQueryResult = function() {
            var query = queryOutputFactory.getOutput($scope.group);
            $rootScope.$broadcast('filterDataWithCqlFilter', query);
        };

        function getGeoServerSettings() {
            self.propertyNames = [];
            LayerService.getGeoServerSettings()
                .then(function(res) {
                    self.geoServerUrl = res.url;
                    setLayers();
                }, errorFn);
        }

        function getCqlFilterUrl(url) {
            var param = window.location.search.split('?').pop();
            if (url && param) {
                var urlParts = url.split('?');
                var filter = 'CQL_FILTER=' + param.replace(/=/gi, '%3D');
                if (urlParts.length == 1) {
                    url = urlParts[0] + '?' + filter;
                } else {
                    url += '&' + filter;
                }
            }
            return url;
        }

        var user_href = window.location.href.split('/');
        function isLayerPage(){
            return _.contains(user_href,"layers");
         }

         function getMapId(){
            if(!isLayerPage()){
                return user_href[4];
            }else 
                return "";
         }

        function getMapOrLayerLoadNonGISData(){
            var data={
                id : isLayerPage() ? layer_info : getMapId(),
                content_type : isLayerPage() ? "layer" : "map",
                activity_type: "load",
                latitude : "",
                longitude : ""
            };
            return data;
        }
        var analyticsNonGISUrl="api/analytics/non-gis/";

        function postMapOrLayerLoadData(){
            analyticsService.postNonGISData(analyticsNonGISUrl,getMapOrLayerLoadNonGISData()).then(function(response){
            
            },function(error){
                console.log(error);
            });
        }        

        var analyticsGISUrl='api/analytics/gis/';
        var postAnalyticsData=$interval( function(){ 
            analyticsService.postGISAnalyticsToServer(analyticsGISUrl);
         }, 60000);
         postMapOrLayerLoadData();

        (getGeoServerSettings)();
        var keyPointerDrag, keySingleClick, keyChangeResolution,keyMoveEnd;
        (function() {

            
            function getAnalyticsGISData(coordinateArray,activityType){
                var data={
                    layer_id:undefined,
                    map_id:undefined,
                    activity_type : activityType,
                    latitude: coordinateArray[1],
                    longitude : coordinateArray[0]
                };
                return data;
            }

            function setMapAndLayerId(analyticsData){
                if(isLayerPage()){
                    analyticsData.layer_id=layer_info;
                }else{
                    analyticsData.map_id=user_href[4];
                }
                return analyticsData;
            }

            var resolutionChanged=false;

            function onMoveEnd(evt) {
                if(resolutionChanged){
                    //to something
                    var mapCenter= ol.proj.transform(map.getView().getCenter(), 'EPSG:3857','EPSG:4326');
                    var analyticsData=getAnalyticsGISData(mapCenter,"zoom");
                    analyticsData=setMapAndLayerId(analyticsData);
                    resolutionChanged=false;
                    analyticsService.saveGISAnalyticsToLocalStorage(analyticsData);
                }
              }

            function onPointerDrag(evt){
                var dragCoordinate=ol.proj.transform(evt.coordinate, 'EPSG:3857','EPSG:4326');
                var analyticsData=getAnalyticsGISData(dragCoordinate,"pan");
                analyticsData=setMapAndLayerId(analyticsData);
                analyticsService.saveGISAnalyticsToLocalStorage(analyticsData);
            }
            function singleClick(evt){
                var clickCoordinate=ol.proj.transform(evt.coordinate, 'EPSG:3857','EPSG:4326');
                var analyticsData=getAnalyticsGISData(clickCoordinate,"click");
                analyticsData=setMapAndLayerId(analyticsData);
                analyticsService.saveGISAnalyticsToLocalStorage(analyticsData);
            }
            keyMoveEnd=map.on('moveend', onMoveEnd);
            keyPointerDrag=map.on('pointerdrag', onPointerDrag);
            keyChangeResolution = map.getView().on('change:resolution', function(evt) {
                    resolutionChanged=true;
            });
            keySingleClick=map.on('singleclick', singleClick);
        })();

        $scope.$on("$destroy", function() {
            ol.Observable.unByKey(keyPointerDrag);
            ol.Observable.unByKey(keySingleClick);
            ol.Observable.unByKey(keyChangeResolution);
            ol.Observable.unByKey(keyMoveEnd);
            $interval.cancel(postAnalyticsData);
        });
    }

})();