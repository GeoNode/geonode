mapModule.directive('locationSearch', [
    'mapTools', '$timeout', '$document',
    function (mapTools, $timeout, $document) {
        return {
            restrict: 'EA',
            scope: {},
            templateUrl: '/static/Templates/Tools/Map/locationSearch.html',
            link: function (scope) {
                var _searchTool = mapTools.search;

                scope.model = { queryString: '' };
                scope.showSearchBox = false;
                scope.loadingResult = false;
                scope.searchBoxClicked = function (event) {
                    event.stopPropagation();
                };

                scope.tooggleSearchBox = function () {
                    scope.showSearchBox = !scope.showSearchBox;
                    if (scope.showSearchBox) {
                        $timeout(function () {
                            document.querySelector('#address-search-box').focus();
                        });
                    }
                };

                scope.search = function () {
                    return _searchTool.search(scope.model.queryString);
                };

                scope.showLocation = function (result) {
                    _searchTool.showLocation(result);
                };

                scope.clearSearch = function () {
                    scope.model.queryString = '';
                    _searchTool.clearLocation();
                };

                $document.on('click', function () {
                    $timeout(function () {
                        scope.showSearchBox = false;
                    });
                });
            }
        };
    }
]);