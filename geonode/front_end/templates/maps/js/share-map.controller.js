(function() {
    'use strict';
    appModule
        .controller('ShareMapController', ShareMapController);

    ShareMapController.$inject = ['$modalInstance', '$window','analyticsService'];

    function ShareMapController($modalInstance, $window,analyticsService) {
        var self = this;

        function initialize() {
            self.height = 100;
            self.width = 100;

            self.url = '';

            self.mapSizes = [{
                    name: 'Mini',
                    height: 100,
                    width: 100,
                },
                {
                    name: 'Small',
                    height: 200,
                    width: 200,
                }, {
                    name: 'Large',
                    height: 400,
                    width: 400,
                }, {
                    name: 'Premium',
                    height: 800,
                    width: 800,
                }
            ];
            self.selectedSize = self.mapSizes[0];
            self.getUrl();
        }

        function postMapShareAnalyticsData(){
            var user_href = window.location.href.split('/');
            var mapId=user_href[4];
            var data={
                id : mapId,
                content_type : "map",
                activity_type: "share",
                latitude : undefined,
                longitude : undefined
            };
            return analyticsService.postNonGISData('api/analytics/non-gis/',data);
        }

        self.getUrl = function() {
            var re = /\d+/g;
            var href = $window.location.pathname;
            if (!re.test(href))
                return;
            var id = href.match(re).pop();
            
            self.url = '<iframe style="border: none;" height="' + self.height + '" width="' + self.width + '" src="'+$window.location.origin+'/maps/' + id + '/embed"></iframe>';
        };

        self.onMapSizeChange = function(size) {
            self.height = size.height;
            self.width = size.width;
            self.getUrl();
        };

        self.closeDialog = function() {
            $modalInstance.close();
        };

        self.init = function(){
            initialize();
            postMapShareAnalyticsData();
        };
    }
})();