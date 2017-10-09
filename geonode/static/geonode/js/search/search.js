'use strict';

(function(){

  var module = angular.module('geonode_main_search', [], function($locationProvider) {
      if (window.navigator.userAgent.indexOf("MSIE") == -1){
          $locationProvider.html5Mode({
            enabled: true,
            requireBase: false
          });

          // make sure that angular doesn't intercept the page links
          angular.element("a").prop("target", "_self");
      }
    });

    // Used to set the class of the filters based on the url parameters
    module.set_initial_filters_from_query = function (data, url_query, filter_param){
        for(var i=0;i<data.length;i++){
            if( url_query == data[i][filter_param] || url_query.indexOf(data[i][filter_param] ) != -1){
                data[i].active = 'active';
            }else{
                data[i].active = '';
            }
        }
        return data;
    }

  // Load categories, keywords, and regions
  module.load_categories = function ($http, $rootScope, $location){
        var params = typeof FILTER_TYPE == 'undefined' ? {} : {'type': FILTER_TYPE};
        if ($location.search().hasOwnProperty('title__icontains')){
          params['title__icontains'] = $location.search()['title__icontains'];
        }
        $http.get(CATEGORIES_ENDPOINT, {params: params}).success(function(data){
            if($location.search().hasOwnProperty('category__identifier__in')){
                data.objects = module.set_initial_filters_from_query(data.objects,
                    $location.search()['category__identifier__in'], 'identifier');
            }
            $rootScope.categories = data.objects;
            $rootScope.$broadcast('broadcast-apply-filters', { category: true });
            if (HAYSTACK_FACET_COUNTS && $rootScope.query_data) {
                module.haystack_facets($http, $rootScope, $location);
            }
        });
    }

  module.load_keywords = function ($http, $rootScope, $location){
        var params = typeof FILTER_TYPE == 'undefined' ? {} : {'type': FILTER_TYPE};
        if ($location.search().hasOwnProperty('title__icontains')){
          params['title__icontains'] = $location.search()['title__icontains'];
        }
        $http.get(KEYWORDS_ENDPOINT, {params: params}).success(function(data){
            if($location.search().hasOwnProperty('keywords__slug__in')){
                data.objects = module.set_initial_filters_from_query(data.objects,
                    $location.search()['keywords__slug__in'], 'slug');
            }
            $rootScope.keywords = data.objects;
            $rootScope.$broadcast('broadcast-apply-filters', { key_word: true });
            if (HAYSTACK_FACET_COUNTS && $rootScope.query_data) {
                module.haystack_facets($http, $rootScope, $location);
            }
        });
    }

  module.load_regions = function ($http, $rootScope, $location){
        var params = typeof FILTER_TYPE == 'undefined' ? {} : {'type': FILTER_TYPE};
        if ($location.search().hasOwnProperty('title__icontains')){
          params['title__icontains'] = $location.search()['title__icontains'];
        }
        $http.get(REGIONS_ENDPOINT, {params: params}).success(function(data){
            if($location.search().hasOwnProperty('regions__name__in')){
                data.objects = module.set_initial_filters_from_query(data.objects,
                    $location.search()['regions__name__in'], 'name');
            }
            $rootScope.regions = data.objects;
            if (HAYSTACK_FACET_COUNTS && $rootScope.query_data) {
                module.haystack_facets($http, $rootScope, $location);
            }
        });
    }

  module.load_owners = function ($http, $rootScope, $location){
    var params = typeof FILTER_TYPE == 'undefined' ? {} : {'type': FILTER_TYPE};
    if ($location.search().hasOwnProperty('title__icontains')){
        params['title__icontains'] = $location.search()['title__icontains'];
    }
    $http.get(OWNERS_ENDPOINT, {params: params}).success(function(data){
        if($location.search().hasOwnProperty('owner__username__in')){
            data.objects = module.set_initial_filters_from_query(data.objects,
                $location.search()['owner__username__in'], 'identifier');
        }
        $rootScope.owners = data.objects;
        if (HAYSTACK_FACET_COUNTS && $rootScope.query_data) {
            module.haystack_facets($http, $rootScope, $location);
        }
    });
  }

  // Update facet counts for categories and keywords
  module.haystack_facets = function($http, $rootScope, $location) {
      var data = $rootScope.query_data;
      if ("categories" in $rootScope) {
          $rootScope.category_counts = data.meta.facets.category;
          for (var id in $rootScope.categories) {
              var category = $rootScope.categories[id];
              if (category.identifier in $rootScope.category_counts) {
                  category.count = $rootScope.category_counts[category.identifier]
              } else {
                  category.count = 0;
              }
          }
      }

      if ("keywords" in $rootScope) {
          $rootScope.keyword_counts = data.meta.facets.keywords;
          for (var id in $rootScope.keywords) {
              var keyword = $rootScope.keywords[id];
              if (keyword.slug in $rootScope.keyword_counts) {
                  keyword.count = $rootScope.keyword_counts[keyword.slug]
              } else {
                  keyword.count = 0;
              }
          }
      }

      if ("regions" in $rootScope) {
          $rootScope.regions_counts = data.meta.facets.regions;
          for (var id in $rootScope.regions) {
              var region = $rootScope.regions[id];
              if (region.name in $rootScope.region_counts) {
                  region.count = $rootScope.region_counts[region.name]
              } else {
                  region.count = 0;
              }
          }
      }

      if ("owners" in $rootScope) {
          $rootScope.owner_counts = data.meta.facets.owners;
          for (var id in $rootScope.owners) {
              var owner = $rootScope.owners[id];
              if (owner.name in $rootScope.owner_counts) {
                  owner.count = $rootScope.owner_counts[owner.name]
              } else {
                  owner.count = 0;
              }
          }
      }
  }

  /*
  * Load categories and keywords
  */
  module.run(function($http, $rootScope, $location){
    /*
    * Load categories and keywords if the filter is available in the page
    * and set active class if needed
    */
    if ($('#categories').length > 0){
       module.load_categories($http, $rootScope, $location);
    }
    if ($('#keywords').length > 0){
       module.load_keywords($http, $rootScope, $location);
    }
    if ($('#regions').length > 0){
       module.load_regions($http, $rootScope, $location);
    }
    if ($('#owners').length > 0){
       module.load_owners($http, $rootScope, $location);
    }


    // Activate the type filters if in the url
    if($location.search().hasOwnProperty('type__in')){
      var types = $location.search()['type__in'];
      if(types instanceof Array){
        for(var i=0;i<types.length;i++){
          $('body').find("[data-filter='type__in'][data-value="+types[i]+"]").addClass('active');
        }
      }else{
        $('body').find("[data-filter='type__in'][data-value="+types+"]").addClass('active');
      }
    }

    // Activate the sort filter if in the url
    if($location.search().hasOwnProperty('order_by')){
      var sort = $location.search()['order_by'];
      $('body').find("[data-filter='order_by']").removeClass('selected');
      $('body').find("[data-filter='order_by'][data-value="+sort+"]").addClass('selected');
    }

  });

  /*
  * Main search controller
  * Load data from api and defines the multiple and single choice handlers
  * Syncs the browser url with the selections
  */
  module.controller('geonode_search_controller', function($injector, $rootScope, $scope, $location, $http, $window, Configs){
    $scope.filterCategoryEnable = false;
    $scope.filterKeywordEnable = false;
    $scope.GD_APPLY_FILTERS = {};
    $scope.pageViewing = "grid";// "list"; // grid
    $scope.STATIC_URL = JS_STATIC_URL; // grid
    $scope.query = $location.search();
    $scope.query.limit = $scope.query.limit || CLIENT_RESULTS_LIMIT;
    $scope.query.offset = $scope.query.offset || 0;
    $scope.page = Math.round(($scope.query.offset / $scope.query.limit) + 1);

    //Get data from apis and make them available to the page
    function query_api(data){
      /*if (!$scope.query.hasOwnProperty("order_by")){
        $scope.query["order_by"] = '-popular_count';
      }*/
      $http.get(Configs.url, {params: data || {}}).success(function(data){
        $scope.results = data.objects;
        $("#load_apply_filter_box").show();
        $scope.total_counts = data.meta.total_count;
        $scope.$root.query_data = data;
        if (HAYSTACK_SEARCH) {
          if ($location.search().hasOwnProperty('q')){
            $scope.text_query = $location.search()['q'].replace(/\+/g," ");
          }
        } else {
          if ($location.search().hasOwnProperty('title__icontains')){
            $scope.text_query = $location.search()['title__icontains'].replace(/\+/g," ");
          }
        }

        //Update facet/keyword/category counts from search results
        if (HAYSTACK_FACET_COUNTS){
            module.haystack_facets($http, $scope.$root, $location);
            $("#types").find("a").each(function(){
                if ($(this)[0].id in data.meta.facets.subtype) {
                    $(this).find("span").text(data.meta.facets.subtype[$(this)[0].id]);
                }
                else if ($(this)[0].id in data.meta.facets.type) {
                    $(this).find("span").text(data.meta.facets.type[$(this)[0].id]);
                } else {
                    $(this).find("span").text("0");
                }
            });
        }
      });
    };
    query_api($scope.query);

    $scope.layerEnable = function(){
        var resource_type = $scope.query['resource_type__in'];
        if(typeof resource_type === 'string' && resource_type=='layer'){
            return true;
        } else if(resource_type instanceof Array) {
            for(var i=0;i<resource_type.length;i++){
                if(resource_type[i] == 'layer'){
                    return true;
                }
            }
        }
        return false;
    }
    $scope.layerEnableClass = ($scope.layerEnable() == true) ? "active" : "";
    $scope.mapEnable = function(){
        var resource_type = $scope.query['resource_type__in'];
        if(typeof resource_type === 'string' && resource_type=='map'){
            return true;
        } else if(resource_type instanceof Array) {
            for(var i=0;i<resource_type.length;i++){
                if(resource_type[i] == 'map'){
                    return true;
                }
            }
        }

        return false;
    }
    $scope.mapEnableClass = ($scope.mapEnable() == true) ? "active" : "";
    $scope.docEnable = function(){
        var resource_type = $scope.query['resource_type__in'];
        if(typeof resource_type === 'string' && resource_type=='document'){
            return true;
        } else if(resource_type instanceof Array) {
            for(var i=0;i<resource_type.length;i++){
                if(resource_type[i] == 'document'){
                    return true;
                }
            }
        }

        return false;
    }
    $scope.docEnableClass = ($scope.docEnable() == true) ? "active" : "";

    $scope.applyAdvancedSearch = function (){
        if($scope.text_query != ""){
            $scope.query['title__icontains'] = $scope.text_query;
        } else {
            delete $scope.query['title__icontains'];
        }
        var region_search_input = $('#region_search_input').val();
        if(region_search_input != ""){
            $scope.query['regions__name__in'] = region_search_input;
        } else {
            delete $scope.query['regions__name__in'];
        }
        //console.log("text_query", $scope.text_query);
        var absUrl = $location.absUrl();
        absUrl = absUrl.replace('/layers/', '/search/').replace('/maps/', '/search/').replace('/documents/', '/search/');
        $window.location.href = absUrl;
        console.log("query", $location.absUrl(), absUrl);

        $scope.do_apply_filters();

        //$scope.$apply();
        $("#gd-advanced-search").slideUp("slow");
    }
    $scope.do_apply_filters = function() {
        // apply filter
        var gdApplyFilters = {};
        var date_gte = $scope.query['date__gte'];
        var date_lte = $scope.query['date__lte'];
        var dateRange = $scope.query['date__range'];
        var dateRangeItems = null;
        if (dateRange != undefined) {
            dateRangeItems = dateRange.split(",");
            gdApplyFilters.dateRange = true;
            gdApplyFilters.date__gte = dateRangeItems[0];
            gdApplyFilters.date__lte = dateRangeItems[1];
        } else if(date_gte != undefined){
            gdApplyFilters.dateRange = true;
            gdApplyFilters.date__gte = date_gte;
        } else if(date_lte != undefined){
            gdApplyFilters.dateRange = true;
            gdApplyFilters.date__lte = date__lte;
        }
        gdApplyFilters.APPLY_FILTER_ENABLE = false;
        gdApplyFilters.categoryEnable = false;
        gdApplyFilters.keywordsEnable = false;
        gdApplyFilters.regionsName = false;
        gdApplyFilters.dateRange = false;
        gdApplyFilters.textQuery = false;

        gdApplyFilters.category_items = [];
        gdApplyFilters.keyword_items = [];

        if($scope.query['title__icontains'] != undefined)
        {
            gdApplyFilters.textQuery = true;
            gdApplyFilters.text_query = $scope.query['title__icontains'];
        }
        if($scope.query['regions__name__in'] != undefined)
        {
            gdApplyFilters.regionsName = true;
            gdApplyFilters.regions__name__in = $scope.query['regions__name__in'];
        }
        if($scope.filterCategoryEnable && $scope.query['category__identifier__in'] != undefined)
        {
            gdApplyFilters.categoryEnable = true;
            var categories = $rootScope.categories;
            var categoryItems = $scope.query['category__identifier__in'];
            for(var i=0; i<categories.length; i++){
                var categorie = deepClone(categories[i]);
                for(var j=0; j<categoryItems.length; j++){
                    if(categorie.identifier == categoryItems[j]){
                        //$rootScope.categories[i]
                        gdApplyFilters.category_items.push(categorie);
                    }
                }
            }
        }
        if($scope.filterKeywordEnable && $scope.query['keywords__slug__in'] != undefined)
        {
            gdApplyFilters.keywordsEnable = true;
            var keywords = $rootScope.keywords;
            var keywordItems = $scope.query['keywords__slug__in'];
            for(var i=0; i<keywords.length; i++){
                var keyword = deepClone(keywords[i]);
                for(var j=0; j<keywordItems.length; j++){
                    if(keyword.slug == keywordItems[j]){
                        gdApplyFilters.keyword_items.push(keyword);
                    }
                }
            }
        }

        if(gdApplyFilters.categoryEnable || gdApplyFilters.keywordsEnable ||
            gdApplyFilters.regionsName || gdApplyFilters.dateRange || gdApplyFilters.textQuery
        ){
            gdApplyFilters.APPLY_FILTER_ENABLE = true;
        }

        $scope.GD_APPLY_FILTERS = deepClone(gdApplyFilters);
        console.log("GD_APPLY_FILTERS",$scope.GD_APPLY_FILTERS);
    };
    $scope.removeTextQuery = function(){
        $scope.text_query = "";
        delete $scope.query['title__icontains'];
        query_api($scope.query);
        $scope.do_apply_filters();
    }
    $scope.$on('broadcast-apply-filters', function(event, args) {
        //var anyThing = args.any;
        // do what you want to do
        //console.log("called-broadcast-apply-filters");
        if($scope.filterCategoryEnable == false && args.category != undefined){
            $scope.filterCategoryEnable = args.category;
        }
        if($scope.filterKeywordEnable == false && args.key_word != undefined){
            $scope.filterKeywordEnable = args.key_word;
        }
        setTimeout($scope.do_apply_filters, 100);
    });
    setTimeout($scope.do_apply_filters, 1500);


    $scope.displayView = function(type){
        $scope.pageViewing = type;
    };
    /*
    * Pagination
    */
    // Control what happens when the total results change
    $scope.$watch('total_counts', function(){
      $scope.numpages = Math.round(
        ($scope.total_counts / $scope.query.limit) + 0.49
      );

      // In case the user is viewing a page > 1 and a
      // subsequent query returns less pages, then
      // reset the page to one and search again.
      if($scope.numpages < $scope.page){
        $scope.page = 1;
        $scope.query.offset = 0;
        query_api($scope.query);
      }

      // In case of no results, the number of pages is one.
      if($scope.numpages == 0){$scope.numpages = 1};
    });

    $scope.paginate_down = function(){
      if($scope.page > 1){
        $scope.page -= 1;
        $scope.query.offset =  $scope.query.limit * ($scope.page - 1);
        query_api($scope.query);
      }
    }

    $scope.paginate_up = function(){
        $scope.numpages = Math.round(
        ($scope.total_counts / $scope.query.limit) + 0.49
      );

      if($scope.numpages > $scope.page){
        $scope.page += 1;
        $scope.query.offset = $scope.query.limit * ($scope.page - 1);
        query_api($scope.query);
      }
    }
    /*
    * End pagination
    */


    if (!Configs.hasOwnProperty("disableQuerySync")) {
        // Keep in sync the page location with the query object
        $scope.$watch('query', function(){
          $location.search($scope.query);
        }, true);
    }

    /*
    * Add the selection behavior to the element, it adds/removes the 'active' class
    * and pushes/removes the value of the element from the query object
    */
    $scope.advanced_search_choice_listener = function($event){
      var element = $($event.target);
      var query_entry = [];
      var data_filter = element.attr('data-filter');
      var value = element.attr('data-value');

      // If the query object has the record then grab it
      if ($scope.query.hasOwnProperty(data_filter)){

        // When in the location are passed two filters of the same
        // type then they are put in an array otherwise is a single string
        if ($scope.query[data_filter] instanceof Array){
          query_entry = $scope.query[data_filter];
        }else{
          query_entry.push($scope.query[data_filter]);
        }
      }

      // If the element is active active then deactivate it
      if(element.hasClass('active')){
        // clear the active class from it
        element.removeClass('active');

        // Remove the entry from the correct query in scope

        query_entry.splice(query_entry.indexOf(value), 1);
      }
      // if is not active then activate it
      else if(!element.hasClass('active')){
        // Add the entry in the correct query
        if (query_entry.indexOf(value) == -1){
          query_entry.push(value);
        }
        element.addClass('active');
      }

      //save back the new query entry to the scope query
      $scope.query[data_filter] = query_entry;

      //if the entry is empty then delete the property from the query
      if(query_entry.length == 0){
        delete($scope.query[data_filter]);
      }
      //query_api($scope.query);
    }

    $scope.multiple_choice_listener = function($event){
      var element = $($event.target);
      var query_entry = [];
      var data_filter = element.attr('data-filter');
      var value = element.attr('data-value');
      var remove = element.attr('do-remove');
      var removeID = element.attr('remove-id');
      var unselectID = element.attr('unselect-id');

      // If the query object has the record then grab it
      if ($scope.query.hasOwnProperty(data_filter)){

        // When in the location are passed two filters of the same
        // type then they are put in an array otherwise is a single string
        if ($scope.query[data_filter] instanceof Array){
          query_entry = $scope.query[data_filter];
        }else{
          query_entry.push($scope.query[data_filter]);
        }
      }

      // If the element is active active then deactivate it
      if(element.hasClass('active')){
        // clear the active class from it
        element.removeClass('active');
        if(remove == 'true'){
            $("#"+removeID).remove();
            $("#"+unselectID).removeClass('active');
            $("#"+unselectID).prop('checked', false); // Unchecks it
        }

        // Remove the entry from the correct query in scope

        query_entry.splice(query_entry.indexOf(value), 1);
      }
      // if is not active then activate it
      else if(!element.hasClass('active')){
        // Add the entry in the correct query
        if (query_entry.indexOf(value) == -1){
          query_entry.push(value);
        }
        element.addClass('active');
      }

      //save back the new query entry to the scope query
      $scope.query[data_filter] = query_entry;

      //if the entry is empty then delete the property from the query
      if(query_entry.length == 0){
        delete($scope.query[data_filter]);
      }
      query_api($scope.query);
      if(remove == 'true'){
        $scope.do_apply_filters();
      }
    }

    $scope.single_choice_listener = function($event){
      var element = $($event.target);
      var query_entry = [];
      var data_filter = element.attr('data-filter');
      var value = element.attr('data-value');

      // If the query object has the record then grab it
      if ($scope.query.hasOwnProperty(data_filter)){
        query_entry = $scope.query[data_filter];
      }

      if(!element.hasClass('selected')){
        // Add the entry in the correct query
        query_entry = value;

        // clear the active class from it
        element.parents('ul').find('a').removeClass('selected');

        element.addClass('selected');

        //save back the new query entry to the scope query
        $scope.query[data_filter] = query_entry;

        query_api($scope.query);
      }
      $("#currtenSortTitle").html($('#profileSortId ul li a.selected').html());
    }

    $scope.limit_choice_listener = function(limit){
        $scope.page = 1;
        $scope.query.limit = limit;
        $scope.query.offset = 0;

        $scope.numpages = Math.round(
            ($scope.total_counts / $scope.query.limit) + 0.49
        );
        query_api($scope.query);
        $("#limitOfpage").html($scope.query.limit);
    };

    /*
    * Text search management
    */
    var text_autocomplete = $('#text_search_input').yourlabsAutocomplete({
          url: AUTOCOMPLETE_URL_RESOURCEBASE,
          choiceSelector: 'span',
          hideAfter: 200,
          minimumCharacters: 1,
          placeholder: gettext('Enter your text here ...'),
          autoHilightFirst: false
    });

    $('#text_search_input').keypress(function(e) {
      if(e.which == 13) {
        $('#text_search_btn').click();
        $('.yourlabs-autocomplete').hide();
      }
    });

    $('#text_search_input').bind('selectChoice', function(e, choice, text_autocomplete) {
          if(choice[0].children[0] == undefined) {
              $('#text_search_input').val($(choice[0]).text());
              $('#text_search_btn').click();
          }
    });

    $('#text_search_btn').click(function(){
        if (HAYSTACK_SEARCH)
            $scope.query['q'] = $('#text_search_input').val();
        else
            $scope.query['title__icontains'] = $('#text_search_input').val();
        query_api($scope.query);
    });

    /*
    * Region search management
    */
    var region_autocomplete = $('#region_search_input').yourlabsAutocomplete({
          url: AUTOCOMPLETE_URL_REGION,
          choiceSelector: 'span',
          hideAfter: 200,
          minimumCharacters: 1,
          appendAutocomplete: $('#region_search_input'),
          placeholder: gettext('Enter your region here ...')
    });
    $('#region_search_input').bind('selectChoice', function(e, choice, region_autocomplete) {
          if(choice[0].children[0] == undefined) {
              $('#region_search_input').val(choice[0].innerHTML);
              $('#region_search_btn').click();
          }
    });

    $('#region_search_btn').click(function(){
        $scope.query['regions__name__in'] = $('#region_search_input').val();
        query_api($scope.query);
    });

    $scope.feature_select = function($event){
      var element = $($event.target);
      var article = $(element.parents('article')[0]);
      if (article.hasClass('resource_selected')){
        element.html('Select');
        article.removeClass('resource_selected');
      }
      else{
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
    $scope.$watch('date_query', function(){
      if($scope.date_query.date__gte != '' && $scope.date_query.date__lte != ''){
        $scope.query['date__range'] = $scope.date_query.date__gte + ',' + $scope.date_query.date__lte;
        delete $scope.query['date__gte'];
        delete $scope.query['date__lte'];
      }else if ($scope.date_query.date__gte != ''){
        $scope.query['date__gte'] = $scope.date_query.date__gte;
        delete $scope.query['date__range'];
        delete $scope.query['date__lte'];
      }else if ($scope.date_query.date__lte != ''){
        $scope.query['date__lte'] = $scope.date_query.date__lte;
        delete $scope.query['date__range'];
        delete $scope.query['date__gte'];
      }else{
        delete $scope.query['date__range'];
        delete $scope.query['date__gte'];
        delete $scope.query['date__lte'];
      }
      if (!init_date){
        query_api($scope.query);
      }else{
        init_date = false;
      }

    }, true);

    $scope.advanced_date_query = {
      'date__gte': '',
      'date__lte': ''
    };
    // advanced_date_query
    var init_date = true;
    $scope.$watch('advanced_date_query', function(){
      if($scope.advanced_date_query.date__gte != '' && $scope.advanced_date_query.date__lte != ''){
        $scope.query['date__range'] = $scope.advanced_date_query.date__gte + ',' + $scope.advanced_date_query.date__lte;
        delete $scope.query['date__gte'];
        delete $scope.query['date__lte'];
      }else if ($scope.advanced_date_query.date__gte != ''){
        $scope.query['date__gte'] = $scope.advanced_date_query.date__gte;
        delete $scope.query['date__range'];
        delete $scope.query['date__lte'];
      }else if ($scope.advanced_date_query.date__lte != ''){
        $scope.query['date__lte'] = $scope.advanced_date_query.date__lte;
        delete $scope.query['date__range'];
        delete $scope.query['date__gte'];
      }else{
        delete $scope.query['date__range'];
        delete $scope.query['date__gte'];
        delete $scope.query['date__lte'];
      }
      if (!init_date){
        //query_api($scope.query);
      }else{
        init_date = false;
      }

    }, true);

    /*
    * Spatial search
    */
    if ($('.leaflet_map').length > 0) {
      angular.extend($scope, {
        layers: {
          baselayers: {
            stamen: {
              name: 'Toner Lite',
              type: 'xyz',
              url: 'http://{s}.tile.stamen.com/toner-lite/{z}/{x}/{y}.png',
              layerOptions: {
                subdomains: ['a', 'b', 'c'],
                attribution: 'Map tiles by <a href="http://stamen.com">Stamen Design</a>',
                continuousWorld: true
              }
            }
          }
        },
        map_center: {
          lat: 23.8103,
          lng: 90.4125,
          zoom: 5
        },
        defaults: {
          zoomControl: false
        }
      });


      var leafletData = $injector.get('leafletData'),
          map = leafletData.getMap('filter-map');

      map.then(function(map){
        map.on('moveend', function(){
          $scope.query['extent'] = map.getBounds().toBBoxString();
          //query_api($scope.query);
        });
      });

      var showMap = false;
      $('#_extent_filter, #advanced-search-control, .advanced-search-control').click(function(evt) {
     	  showMap = !showMap
        if (showMap){
          leafletData.getMap().then(function(map) {
            map.invalidateSize();
          });
        }

      });
    }
    $("#limitOfpage").html($scope.query.limit);

    //featured section

    $scope.featuredFunction = function(datalayerID,datastatusID){

            var data_layerID = datalayerID;
            var data_statusID = datastatusID;
                var JS_STATIC_URL = "../api/make-featured/";
                   var qID = data_layerID;
                   var qsID = data_statusID;
                    var data = JSON.stringify({
                    "resource_id": qID,
                    "status": qsID
                });
                $.ajax({
                    cache: false,
                    type: 'POST',
                    url: JS_STATIC_URL,
                    data: data,
                    dataType: "json",
                    success: function(jsondata) {
                        console.log("success");
                        var data = eval(jsondata.objects);
                        $window.location.href = data;
                        $window.location.reload();

                    },
                    error: function(xhr, ajaxOptions, thrownError) {
                        console.log("error");
                    }
                 });
        return false;
    }

    //favourite section

    $scope.favouriteFunction = function(datalayerID,datastatusID){

            var data_layerID = datalayerID;
            var data_statusID = datastatusID;
                var JS_STATIC_URL = "../api/makefavorite/";
                   var qID = data_layerID;
                   var qsID = data_statusID;
                    var data = JSON.stringify({
                    "resource_id": qID,
                    "status": qsID
                });
                $.ajax({
                    cache: false,
                    type: 'POST',
                    url: JS_STATIC_URL,
                    data: data,
                    dataType: "json",
                    success: function(jsondata) {
                        console.log("success");
                        var data = eval(jsondata.objects);
                        $window.location.href = data;
                        $window.location.reload();

                    },
                    error: function(xhr, ajaxOptions, thrownError) {
                        console.log("error");
                    }
                 });
        return false;
    }
    // Organization add favorite section

    $scope.favouriteGroup = function(datalayerID,datastatusID){

            var data_layerID = datalayerID;
            var data_statusID = datastatusID;
                var JS_STATIC_URL = "../api/makefavorite/";
                   var qID = data_layerID;
                   var qsID = data_statusID;
                    var data = JSON.stringify({
                    "group_id": qID,
                    "status": qsID
                });
                $.ajax({
                    cache: false,
                    type: 'POST',
                    url: JS_STATIC_URL,
                    data: data,
                    dataType: "json",
                    success: function(jsondata) {
                        console.log("success");
                        var data = eval(jsondata.objects);
                        $window.location.href = data;
                        $window.location.reload();

                    },
                    error: function(xhr, ajaxOptions, thrownError) {
                        console.log("error");
                    }
                 });
        return false;
    }

  });
})();
