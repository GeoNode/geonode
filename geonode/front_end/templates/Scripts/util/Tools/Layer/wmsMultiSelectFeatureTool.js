mapModule.factory('WmsMultiSelectFeatureTool', [
    'urlResolver',
    'jantrik.Event',
    '$http',
    'SurfFeature',
    function (urlResolver,
        Event,
        $http,
        SurfFeature
        ) {
        function parseId(olFeature) {
            var idParts = (olFeature.getId() || '.').split('.');

            return { dataId: idParts[0], fid: idParts[1] };
        }

        function WmsMultiSelectFeatureTool(olMap, surfMap) {
            this.events = new Event();
            this.surfMap = surfMap;
            this.olMap = olMap;
            this.isActivated = false;
            this.activate();
        }

        function getFeature(event) {
            var _this = this;

            var layers = _this.surfMap.getLayers();

            var dataIds = [];
            var styleIds = [];

            angular.forEach(layers, function (sl) {
                if (sl.IsVisible) {
                    dataIds.push(sl.getDataId());
                    styleIds.push(sl.getStyleName());
                }
            });
            if (dataIds.length === 0) return;
            var size = _this.olMap.getSize();
            var bbox = _this.olMap.getView().calculateExtent(size);
            var layersParamValue = dataIds.join(',');
            
            var urlParams = {
                service: 'wms',
                version: '1.1.0',
                request: 'GetFeatureInfo',
                layers: layersParamValue,
                query_layers: layersParamValue,
                styles: styleIds.join(','),
                srs: 'EPSG:3857',
                bbox: bbox.join(','),
                width: size[0],
                height: size[1],
                info_format: 'application/json',
                exceptions: 'application/json',
                feature_count: 25,
                x: Math.round(event.pixel[0]),
                y: Math.round(event.pixel[1])
            };

            var url = urlResolver.resolveGeoServer('wms', urlParams);
            var findLayer = function (id) {
                return id.dataId;
            }
            $http.get(url).then(function (response) {
                var geoJson = response.data;
                var parser = new ol.format.GeoJSON();
                var olFeatures = parser.readFeatures(geoJson);


                _this.featuresData = olFeatures.map(function (of) {
                    var id = parseId(of);
                    var lookup = {};
                    for (var key in layers) {
                        if (layers.hasOwnProperty(key)) {
                            lookup[layers[key].DataId] = layers[key];
                        }
                    };
                    var surfLayer = lookup[id.dataId];
                    var surfFeature = new SurfFeature(of, surfLayer);
                    return {
                        surfFeature: surfFeature,
                        olFeature: of
                    };
                });
                _this.setSelected(0);


            }).catch(function () {
                //featureReceived(null);
            });

            /* surfRepository.getGeoserver('wms', urlParams).then(function (response) {
                 var surfFeatures = surfFeatureParser.fromGeoJson(response, _this.surfMap);
                 _this.broadcast('selected', surfFeatures, event.coordinate);
             });*/
        }

        WmsMultiSelectFeatureTool.prototype = Object.create(Event.prototype);
        WmsMultiSelectFeatureTool.prototype.constructor = WmsMultiSelectFeatureTool;

        WmsMultiSelectFeatureTool.prototype.activate = function () {
            if (!this.isActivated) {
                this.olMap.on('singleclick', getFeature, this);
                this.isActivated = true;
            }
        };

        WmsMultiSelectFeatureTool.prototype.setSelected = function (index) {

            if (index >= 0 && index < this.featuresData.length) {
                var featureData = this.featuresData[index];
                var selectFeatureTool = featureData.surfFeature.layer.tools.selectFeature.innerTool;
                if (selectFeatureTool)
                    selectFeatureTool.featureReceived(featureData);
                this.selectedIndex = index;
            }
        };

        WmsMultiSelectFeatureTool.prototype.selectNext = function () {
            this.setSelected(this.selectedIndex + 1);
        };

        WmsMultiSelectFeatureTool.prototype.selectPrevious = function () {
            this.setSelected(this.selectedIndex - 1);
        };

        return WmsMultiSelectFeatureTool;
    }
]);
