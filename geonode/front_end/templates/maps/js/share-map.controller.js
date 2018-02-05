(function() {
    'use strict';
    appModule
        .controller('ShareMapController', ShareMapController);

    ShareMapController.$inject = ['$modalInstance', '$window'];

    function ShareMapController($modalInstance, $window) {
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

        self.getUrl = function() {
            var re = /\d+/g;
            var href = $window.location.pathname;
            if (!re.test(href))
                return;
            var id = href.match(re).pop();
            self.url = '<iframe style="border: none;" height="' + self.height + '" width="' + self.width + '" src="https://geodash.gov.bd/maps/' + id + '/embed"></iframe>';
        }

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
           
        };
    }
})();