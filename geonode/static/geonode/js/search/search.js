'use strict';

(function () {

    var module = angular.module('geonode_main_search', [], function ($locationProvider) {
        if (window.navigator.userAgent.indexOf("MSIE") == -1) {
            $locationProvider.html5Mode({
                enabled: true,
                requireBase: false
            });

            // make sure that angular doesn't intercept the page links
            angular.element("a").prop("target", "_self");
        }
    });

    // Used to set the class of the filters based on the url parameters
    module.set_initial_filters_from_query = function (data, url_query, filter_param) {
        for (var i = 0; i < data.length; i++) {
            if (url_query == data[i][filter_param] || url_query.indexOf(data[i][filter_param]) != -1) {
                data[i].active = 'active';
            } else {
                data[i].active = '';
            }
        }
        return data;
    }

    // Load categories, keywords, and regions
    module.load_categories = function ($http, $rootScope, $location) {
        var params = typeof FILTER_TYPE == 'undefined' ? {} : {'type': FILTER_TYPE};
        if ($location.search().hasOwnProperty('title__icontains')) {
            params['title__icontains'] = $location.search()['title__icontains'];
        }
        $http.get(CATEGORIES_ENDPOINT, {params: params}).then(successCallback, errorCallback);

        function successCallback(data) {
            //success code
            if ($location.search().hasOwnProperty('category__identifier__in')) {
                data.data.objects = module.set_initial_filters_from_query(data.data.objects,
                    $location.search()['category__identifier__in'], 'identifier');
            }
            $rootScope.categories = data.data.objects;
        };

        function errorCallback(error) {
            //error code
        };
    }

    // Load group categories
    module.load_group_categories = function ($http, $rootScope, $location) {
        var params = typeof FILTER_TYPE == 'undefined' ? {} : {'type': FILTER_TYPE};
        $http.get(GROUP_CATEGORIES_ENDPOINT, {params: params}).then(successCallback, errorCallback);

        function successCallback(data) {
            //success code
            $rootScope.groupCategories = data.data.objects;
        };

        function errorCallback(error) {
            //error code
        };
    }

    module.load_keywords = function ($http, $rootScope, $location) {
        var params = typeof FILTER_TYPE == 'undefined' ? {} : {'type': FILTER_TYPE};
        if ($location.search().hasOwnProperty('title__icontains')) {
            params['title__icontains'] = $location.search()['title__icontains'];
        }
        $http.get(KEYWORDS_ENDPOINT, {params: params}).then(successCallback, errorCallback);

        function successCallback(data) {
            //success code
            if ($location.search().hasOwnProperty('keywords__slug__in')) {
                data.data.objects = module.set_initial_filters_from_query(data.data.objects,
                    $location.search()['keywords__slug__in'], 'slug');
            }
            $rootScope.keywords = data.data.objects;
        };

        function errorCallback(error) {
            //error code
        };
    }


    module.load_h_keywords = function ($http, $rootScope, $location) {
        var params = typeof FILTER_TYPE == 'undefined' ? {} : {'type': FILTER_TYPE};
        $http.get(H_KEYWORDS_ENDPOINT, {params: params}).then(successCallback, errorCallback);

        function successCallback(data) {
            //success code
            $('#treeview').treeview({
                data: data.data,
                multiSelect: true,
                showIcon: true,
                showCheckbox: false,
                showTags: true,
                tagsClass: 'badge',
                onNodeSelected: function ($event, node) {
                    $rootScope.$broadcast('select_h_keyword', node);
                    if (node.nodes) {
                        for (var i = 0; i < node.nodes.length; i++) {
                            $('#treeview').treeview('selectNode', node.nodes[i]);
                        }
                    }
                },
                onNodeUnselected: function ($event, node) {
                    $rootScope.$broadcast('unselect_h_keyword', node);
                    if (node.nodes) {
                        for (var i = 0; i < node.nodes.length; i++) {
                            $('#treeview').treeview('unselectNode', node.nodes[i]);
                            $('#treeview').trigger('nodeUnselected', $.extend(true, {}, node.nodes[i]));
                        }
                    }
                }
            });
        };

        function errorCallback(error) {
            //error code
            console.log(error);
        };
    };

    module.load_t_keywords = function ($http, $rootScope, $location) {
        var params = typeof FILTER_TYPE == 'undefined' ? {} : {'type': FILTER_TYPE};
        if ($location.search().hasOwnProperty('title__icontains')) {
            params['title__icontains'] = $location.search()['title__icontains'];
        }
        if (enable_thesauri) {
            $http.get(T_KEYWORDS_ENDPOINT, {params: params}).then(successCallback, errorCallback);
        }

        function successCallback(data) {
            //success code
            if ($location.search().hasOwnProperty('tkeywords__id__in')) {
                data.data.objects = module.set_initial_filters_from_query(data.data.objects,
                    $location.search()['tkeywords__id__in'], 'id');
            }
            $rootScope.tkeywords = data.data.objects;
        };

        function errorCallback(error) {
            //error code
            console.log(error);
        };
    }

    module.load_regions = function ($http, $rootScope, $location) {
        var params = typeof FILTER_TYPE == 'undefined' ? {} : {'type': FILTER_TYPE};
        if ($location.search().hasOwnProperty('title__icontains')) {
            params['title__icontains'] = $location.search()['title__icontains'];
        }
        $http.get(REGIONS_ENDPOINT, {params: params}).then(successCallback, errorCallback);

        function successCallback(data) {
            //success code
            if ($location.search().hasOwnProperty('regions__name__in')) {
                data.data.objects = module.set_initial_filters_from_query(data.data.objects,
                    $location.search()['regions__name__in'], 'name');
            }
            $rootScope.regions = data.data.objects;
        };

        function errorCallback(error) {
            //error code
        };
    }

    module.load_groups = function ($http, $rootScope, $location) {
        var params = typeof FILTER_TYPE == 'undefined' ? {} : {'type': FILTER_TYPE};
        $http.get(GROUPS_ENDPOINT, {params: params}).then(successCallback, errorCallback);

        function successCallback(data) {
            //success code
            $rootScope.groups = data.data.objects;
        };

        function errorCallback(error) {
            //error code
        };
    }

    module.load_owners = function ($http, $rootScope, $location) {
        var params = typeof FILTER_TYPE == 'undefined' ? {} : {'type': FILTER_TYPE};
        if ($location.search().hasOwnProperty('title__icontains')) {
            params['title__icontains'] = $location.search()['title__icontains'];
        }
        $http.get(OWNERS_ENDPOINT, {params: params}).then(successCallback, errorCallback);

        function successCallback(data) {
            //success code
            if ($location.search().hasOwnProperty('owner__username__in')) {
                data.data.objects = module.set_initial_filters_from_query(data.data.objects,
                    $location.search()['owner__username__in'], 'identifier');
            }
            $rootScope.owners = data.data.objects;
        };

        function errorCallback(error) {
            //error code
        };
    }

    /*
    * Load categories and keywords
    */
    module.run(function ($http, $rootScope, $location) {
        /*
        * Load categories and keywords if the filter is available in the page
        * and set active class if needed
        */
        if ($('#categories').length > 0) {
            module.load_categories($http, $rootScope, $location);
        }

        if ($('#group-categories').length > 0) {
            module.load_group_categories($http, $rootScope, $location);
        }

        //if ($('#keywords').length > 0){
        //   module.load_keywords($http, $rootScope, $location);
        //}
        module.load_h_keywords($http, $rootScope, $location);

        if ($('#regions').length > 0) {
            module.load_regions($http, $rootScope, $location);
        }
        if ($('#owners').length > 0) {
            module.load_owners($http, $rootScope, $location);
        }
        if ($('#groups').length > 0) {
            module.load_groups($http, $rootScope, $location);
        }
        if ($('#tkeywords').length > 0) {
            module.load_t_keywords($http, $rootScope, $location);
        }


        // Activate the type filters if in the url
        if ($location.search().hasOwnProperty('type__in')) {
            var types = $location.search()['type__in'];
            if (types instanceof Array) {
                for (var i = 0; i < types.length; i++) {
                    $('body').find("[data-filter='type__in'][data-value=" + types[i] + "]").addClass('active');
                }
            } else {
                $('body').find("[data-filter='type__in'][data-value=" + types + "]").addClass('active');
            }
        }

        // Activate the sort filter if in the url
        if ($location.search().hasOwnProperty('order_by')) {
            var sort = $location.search()['order_by'];
            $('body').find("[data-filter='order_by']").removeClass('selected');
            $('body').find("[data-filter='order_by'][data-value=" + sort + "]").addClass('selected');
        }

    });

    /*
    * Main search controller
    * Load data from api and defines the multiple and single choice handlers
    * Syncs the browser url with the selections
    */
    module.controller('geonode_search_controller', function ($injector, $scope, $location, $http, Configs) {
        $scope.query = $location.search();
        $scope.query.limit = $scope.query.limit || CLIENT_RESULTS_LIMIT;
        $scope.query.offset = $scope.query.offset || 0;
        $scope.page = Math.round(($scope.query.offset / $scope.query.limit) + 1);

        //Get data from apis and make them available to the page
        function query_api(data) {
            $http.get(Configs.url, {params: data || {}}).then(successCallback, errorCallback);

            function successCallback(data) {
                //success code
                setTimeout(function () {
                    $('[ng-controller="CartList"] [data-toggle="tooltip"]').tooltip();
                }, 0);
                $scope.results = data.data.objects;
                $scope.total_counts = data.data.meta.total_count;
                $scope.$root.query_data = data.data;

                if ($location.search().hasOwnProperty('title__icontains')) {
                    $scope.text_query = $location.search()['title__icontains'].replace(/\+/g, " ");
                }
                if ($location.search().hasOwnProperty('name__icontains')) {
                    $scope.text_query = $location.search()['name__icontains'].replace(/\+/g, " ");
                }
                if ($location.search().hasOwnProperty('name')) {
                    $scope.text_query = $location.search()['name'].replace(/\+/g, " ");
                }

            };

            function errorCallback(error) {
                //error code
            };
        };
        query_api($scope.query);

        /*
        * Pagination
        */
        // Control what happens when the total results change
        $scope.$watch('total_counts', function () {
            $scope.numpages = Math.round(
                ($scope.total_counts / $scope.query.limit) + 0.49
            );

            // In case the user is viewing a page > 1 and a
            // subsequent query returns less pages, then
            // reset the page to one and search again.
            if ($scope.numpages < $scope.page) {
                $scope.page = 1;
                $scope.query.offset = 0;
                query_api($scope.query);
            }

            // In case of no results, the number of pages is one.
            if ($scope.numpages == 0) {
                $scope.numpages = 1
            }
            ;
        });

        $scope.paginate_down = function () {
            if ($scope.page > 1) {
                $scope.page -= 1;
                $scope.query.offset = $scope.query.limit * ($scope.page - 1);
                query_api($scope.query);
            }
        }

        $scope.paginate_up = function () {
            if ($scope.numpages > $scope.page) {
                $scope.page += 1;
                $scope.query.offset = $scope.query.limit * ($scope.page - 1);
                query_api($scope.query);
            }
        }

        $scope.scroll_top = function () {
            document.body.scrollTop = 0;
            document.documentElement.scrollTop = 0;
        }

        $scope.sync_pagination_scroll = function (up) {
            if (up) {
                const paginate = new Promise(function (resolve, reject) {
                    $scope.paginate_up()
                    resolve(true);
                });
                paginate.then((v) => {
                    $scope.scroll_top()
                })
            } else {
                const paginate = new Promise(function (resolve, reject) {
                    $scope.paginate_down()
                    resolve(true);
                });
                paginate.then((v) => {
                    $scope.scroll_top()
                })
            }

        }
        /*
        * End pagination
        */

        if (!Configs.hasOwnProperty("disableQuerySync")) {
            // Keep in sync the page location with the query object
            $scope.$watch('query', function () {
                $location.search($scope.query);
            }, true);
        }

        // Hierarchical keyword listeners
        $scope.$on('select_h_keyword', function ($event, element) {
            var data_filter = 'keywords__slug__in';
            var query_entry = [];
            var value = (element.href ? element.href : element.text);
            // If the query object has the record then grab it
            if ($scope.query.hasOwnProperty(data_filter)) {

                // When in the location are passed two filters of the same
                // type then they are put in an array otherwise is a single string
                if ($scope.query[data_filter] instanceof Array) {
                    query_entry = $scope.query[data_filter];
                } else {
                    query_entry.push($scope.query[data_filter]);
                }
            }

            // Add the entry in the correct query
            if (query_entry.indexOf(value) == -1) {
                query_entry.push(value);
            }

            //save back the new query entry to the scope query
            $scope.query[data_filter] = query_entry;

            query_api($scope.query);
        });

        $scope.$on('unselect_h_keyword', function ($event, element) {
            var data_filter = 'keywords__slug__in';
            var query_entry = [];
            var value = (element.href ? element.href : element.text);
            // If the query object has the record then grab it
            if ($scope.query.hasOwnProperty(data_filter)) {

                // When in the location are passed two filters of the same
                // type then they are put in an array otherwise is a single string
                if ($scope.query[data_filter] instanceof Array) {
                    query_entry = $scope.query[data_filter];
                } else {
                    query_entry.push($scope.query[data_filter]);
                }
            }

            query_entry.splice(query_entry.indexOf(value), 1);

            //save back the new query entry to the scope query
            $scope.query[data_filter] = query_entry;

            //if the entry is empty then delete the property from the query
            if (query_entry.length == 0) {
                delete ($scope.query[data_filter]);
            }
            query_api($scope.query);
        });

        /*
        * Add the selection behavior to the element, it adds/removes the 'active' class
        * and pushes/removes the value of the element from the query object
        */
        $scope.multiple_choice_listener = function ($event) {
            var element = $($event.currentTarget);
            var query_entry = [];
            var data_filter = element.attr('data-filter');
            var value = element.attr('data-value');

            // If the query object has the record then grab it
            if ($scope.query.hasOwnProperty(data_filter)) {

                // When in the location are passed two filters of the same
                // type then they are put in an array otherwise is a single string
                if ($scope.query[data_filter] instanceof Array) {
                    query_entry = $scope.query[data_filter];
                } else {
                    query_entry.push($scope.query[data_filter]);
                }
            }

            // If the element is active active then deactivate it
            if (element.hasClass('active')) {
                // clear the active class from it
                element.removeClass('active');

                // Remove the entry from the correct query in scope

                query_entry.splice(query_entry.indexOf(value), 1);
            }
            // if is not active then activate it
            else if (!element.hasClass('active')) {
                // Add the entry in the correct query
                if (query_entry.indexOf(value) == -1) {
                    query_entry.push(value);
                }
                element.addClass('active');
            }

            //save back the new query entry to the scope query
            $scope.query[data_filter] = query_entry;

            //if the entry is empty then delete the property from the query
            if (query_entry.length == 0) {
                delete ($scope.query[data_filter]);
            }
            query_api($scope.query);
        }

        $scope.single_choice_listener = function ($event) {
            var element = $($event.currentTarget);
            var query_entry = [];
            var data_filter = element.attr('data-filter');
            var value = element.attr('data-value');
            // Type of data being displayed, use 'content' instead of 'all'
            $scope.dataValue = (value == 'all') ? 'content' : value;

            // If the query object has the record then grab it
            if ($scope.query.hasOwnProperty(data_filter)) {
                query_entry = $scope.query[data_filter];
            }

            if (data_filter === 'app_type__in'){
                delete ($scope.query['type__in']);
            }
            else {
                delete ($scope.query['app_type__in']);
            }

            if (!element.hasClass('selected')) {
                // Add the entry in the correct query
                query_entry = value;

                // clear the active class from it
                element.parents('ul').find('a').removeClass('selected');

                element.addClass('selected');

                //save back the new query entry to the scope query
                $scope.query[data_filter] = query_entry;

                query_api($scope.query);
            }
        }

        $('#text_search_btn').click(function () {
            if (AUTOCOMPLETE_URL_RESOURCEBASE == "/people/autocomplete/") { // updated url to work with new autocomplete backend format
                // a user profile has no title; if search was triggered from
                // the /people page, filter by username instead
                var query_key = 'username__icontains';
            } else if (AUTOCOMPLETE_URL_RESOURCEBASE == "/groups/autocomplete_category/") {
                // Adding in this conditional since both groups autocomplete and searches requests need to search name not title.
                var query_key = 'name__icontains';
            } else if (AUTOCOMPLETE_URL_RESOURCEBASE == "/groups/autocomplete/") {
                // Adding in this conditional since both groups autocomplete and searches requests need to search name not title.
                var query_key = $('#text_search_input').data('query-key') || 'title';
            } else {
                var query_key = $('#text_search_input').data('query-key') || 'title__icontains';
            }
            if ($('#text_search_input').val()) {
                $scope.query[query_key] = $('#text_search_input').val();
            } else {
                // Reset query context
                var limit = $scope.query['limit'];
                var offset = $scope.query['offset'];
                var order_by = $scope.query['order_by'];
                $scope.query = {};
                $scope.query['limit'] = limit;
                $scope.query['offset'] = offset;
                if (order_by) {
                    $scope.query['order_by'] = order_by;
                }
            }
            if ($('#text_search_input').val() || $('#text_search_input').val()) {
                $scope.query['abstract__icontains'] = $('#text_search_input').val();
                $scope.query['purpose__icontains'] = $('#text_search_input').val();
                $scope.query['f_method'] = 'or';
            }
            query_api($scope.query);
        });

        $('#region_search_btn').click(function () {
            if ($('#region_search_input').val()){
                $scope.query['regions__name__in'] = $('#region_search_input').val();
            }
            else {
                delete $scope.query['regions__name__in']
            }
            query_api($scope.query);
        });

        $scope.feature_select = function ($event) {
            var element = $(event.currentTarget);
            var article = $(element.parents('article')[0]);
            if (article.hasClass('resource_selected')) {
                element.html('Select');
                article.removeClass('resource_selected');
            } else {
                element.html('Deselect');
                article.addClass('resource_selected');
            }
        };

        /*
        * Date management
        */

        $scope.date_query = {
            'date__gte': '',
            'date__lte': ''
        };
        var init_date = true;
        $scope.$watch('date_query', function () {
            if ($scope.date_query.date__gte != '' && $scope.date_query.date__lte != '') {
                var dateGte = new Date($scope.date_query.date__gte).toISOString();
                var dateLte = new Date($scope.date_query.date__lte).toISOString();
                $scope.query['date__range'] = dateGte + ',' + dateLte;
                delete $scope.query['date__gte'];
                delete $scope.query['date__lte'];
            } else if ($scope.date_query.date__gte != '') {
                var dateGte = new Date($scope.date_query.date__gte).toISOString();
                $scope.query['date__gte'] = dateGte;
                delete $scope.query['date__range'];
                delete $scope.query['date__lte'];
            } else if ($scope.date_query.date__lte != '') {
                var dateLte = new Date($scope.date_query.date__lte).toISOString();
                $scope.query['date__lte'] = dateLte;
                delete $scope.query['date__range'];
                delete $scope.query['date__gte'];
            } else {
                delete $scope.query['date__range'];
                delete $scope.query['date__gte'];
                delete $scope.query['date__lte'];
            }
            if (!init_date) {
                query_api($scope.query);
            } else {
                init_date = false;
            }

        }, true);

        /*
         * Spatial search
         */
        if ($('.leaflet_map').length > 0) {
            angular.extend($scope, {
                layers: [
                    {
                        name: 'OpenStreetMap',
                        active: true,
                        source: {
                            type: 'OSM'
                        }
                    }
                ],
                center: {
                    lat: 0.0,
                    lon: 0.0,
                    zoom: 1
                },
                defaults: {
                    interactions: {
                        mouseWheelZoom: true
                    },
                    controls: {
                        zoom: {
                            position: 'topleft'
                        }
                    }
                }
            });

            var olData = $injector.get('olData'),
                map = olData.getMap('filter-map');

            map.then(function (map) {
                map.on('moveend', function () {
                    var glbox = map.getView().calculateExtent(map.getSize()); // doesn't look as expected.
                    var box = ol.proj.transformExtent(glbox, 'EPSG:3857', 'EPSG:4326');
                    $scope.query['extent'] = box.toString();
                    query_api($scope.query);
                });
            });

            var showMap = false;
            $('#_extent_filter').click(function (evt) {
                showMap = !showMap
                if (showMap) {
                    olData.getMap().then(function (map) {
                        map.updateSize();
                    });
                }
            });
        }
    });
})();
