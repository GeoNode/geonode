import Search from "app/search/components/Search";
import PubSub from "pubsub-js";
import SelectionTree from "app/search/components/SelectionTree";
import TextSearchForm from "app/search/components/TextSearchForm";
import searchHelpers from "app/search/helpers/searchHelpers";
import angularShim from "app/utils/angularShim";
import locationUtils from "app/utils/locationUtils";

export default (() => {
  const searcher = Search({
    searchURL: "/api/base/"
  });

  /*
    `syncScope` is used as a shim while AngularJS is being phased out of
    the project. The `Search` instance is the single source of truth for
    search state, and the AngularJS $scope object is synced to the instance's
    data model after the query is executed in order to update the view.
  */

  const syncScope = angularShim.syncScope([
    ["page", "currentPage"],
    ["query", "query"],
    ["results", "results"],
    ["total_counts", "resultCount"],
    ["numpages", "numberOfPages"],
    ["text_query", "queryValue"]
  ]);

  const module = angular.module(
    "geonode_main_search",
    [],
    $locationProvider => {
      if (window.navigator.userAgent.indexOf("MSIE") === -1) {
        $locationProvider.html5Mode({
          enabled: true,
          requireBase: false
        });

        // make sure that angular doesn't intercept the page links
        angular.element("a").prop("target", "_self");
      }
    }
  );

  module.load_h_keywords = () => {
    const params =
      typeof FILTER_TYPE === "undefined" ? {} : { type: FILTER_TYPE };
    searchHelpers.fetch(H_KEYWORDS_ENDPOINT, { params }).then(data => {
      SelectionTree({
        id: "treeview",
        data,
        eventId: "h_keyword"
      });
    });
  };

  /*
  * Load categories and keywords
  */
  module.run(($rootScope, $location) => {
    /*
    * Load categories and keywords if the filter is available in the page
    * and set active class if needed
    */
    let requestQueue = [
      {
        id: "categories",
        endpoint: CATEGORIES_ENDPOINT,
        requestParam: "title__icontains",
        filterParam: "category__identifier__in",
        alias: "identifier"
      },
      {
        id: "groupcategories",
        endpoint: GROUP_CATEGORIES_ENDPOINT,
        requestParam: "name__icontains",
        filterParam: "slug",
        alias: "identifier"
      },
      {
        id: "regions",
        endpoint: REGIONS_ENDPOINT,
        requestParam: "title__icontains",
        filterParam: "regions__name__in",
        alias: "name"
      },
      {
        id: "owners",
        endpoint: OWNERS_ENDPOINT,
        requestParam: "title__icontains",
        filterParam: "owner__username__in",
        alias: "identifier"
      },
      {
        id: "tkeywords",
        endpoint: T_KEYWORDS_ENDPOINT,
        requestParam: "title__icontains",
        filterParam: "tkeywords__id__in",
        alias: "id"
      },
      {
        id: "tkeywords",
        endpoint: H_KEYWORDS_ENDPOINT,
        requestParam: "title__icontains",
        filterParam: "tkeywords__id__in",
        alias: "id"
      }
      // Only make the request if a page element possessing the id exists
    ].filter(req => $(`#${req.id}`).length > 0);

    module.load_h_keywords();

    searchHelpers.buildRequestFromParamQueue(requestQueue).then(data => {
      for (let i = 0; i < requestQueue.length; i += 1) {
        $rootScope[requestQueue[i].id] = data[i];
      }
    });

    // Activate the type filters if in the url
    if (locationUtils.paramExists("type__in")) {
      var types = locationUtils.getUrlParam("type__in");
      if (types instanceof Array) {
        for (var i = 0; i < types.length; i++) {
          $("body")
            .find("[data-filter='type__in'][data-value=" + types[i] + "]")
            .addClass("active");
        }
      } else {
        $("body")
          .find("[data-filter='type__in'][data-value=" + types + "]")
          .addClass("active");
      }
    }

    // Activate the sort filter if in the url
    if ($location.search().hasOwnProperty("order_by")) {
      var sort = $location.search()["order_by"];
      $("body")
        .find("[data-filter='order_by']")
        .removeClass("selected");
      $("body")
        .find("[data-filter='order_by'][data-value=" + sort + "]")
        .addClass("selected");
    }
  });

  /*
  * Main search controller
  * Load data from api and defines the multiple and single choice handlers
  * Syncs the browser url with the selections
  */
  module.controller("geonode_search_controller", function(
    $injector,
    $scope,
    $location,
    Configs
  ) {
    searcher.set("query", locationUtils.getUrlParams());
    searcher.setQueryProp(
      "limit",
      searcher.getQueryProp("limit") || CLIENT_RESULTS_LIMIT
    );
    searcher.setQueryProp("offset", searcher.getQueryProp("offset") || 0);
    searcher.set(
      "currentPage",
      Math.round(
        searcher.getQueryProp("offset") / searcher.getQueryProp("limit") + 1
      )
    );

    /*
    * Text search management
    */

    const textSearchInstance = TextSearchForm({
      url: AUTOCOMPLETE_URL_RESOURCEBASE,
      id: "text_search"
    });

    PubSub.subscribe("textSearchClick", (event, data) => {
      searcher.setQueryProp(data.key, data.val);
      query_api(searcher.get("query"));
    });

    // Get data from apis and make them available to the page
    function query_api(params) {
      searcher.search(params).then(data => {
        setTimeout(() => {
          $('[ng-controller="CartList"] [data-toggle="tooltip"]').tooltip();
        });
        const queryValue = (textSearchInstance.getFormVal()
          ? textSearchInstance.getFormVal()
          : locationUtils.paramExists("title__icontains")
            ? locationUtils.getUrlParam("title__icontains")
            : ""
        ).replace(/\+/g, " ");
        searcher.set("queryValue", queryValue);
        syncScope($scope, searcher);
      });
    }
    query_api(searcher.get("query"));

    /*
    * Pagination
    */
    // Control what happens when the total results change
    const handleResultChange = () => {
      let numpages = searcher.calculateNumberOfPages(
        searcher.get("resultCount"),
        searcher.getQueryProp("limit")
      );
      searcher.set("numberOfPages", numpages);
      // In case the user is viewing a page > 1 and a
      // subsequent query returns less pages, then
      // reset the page to one and search again.
      if (searcher.get("numberOfPages") < searcher.get("currentPage")) {
        searcher.set("currentPage", 1);
        searcher.setQueryProp("offset", 0);
        query_api(searcher.get("query"));
      }

      // In case of no results, the number of pages is one.
      if (searcher.get("numberOfPages") === 0) {
        searcher.set("numberOfPages", 1);
      }
      syncScope($scope, searcher);
    };

    $scope.$watch("total_counts", handleResultChange);

    $scope.paginate_down = function() {
      if (searcher.get("currentPage") > 1) {
        searcher.decrementCurrentPage();
        searcher.setQueryProp(
          "offset",
          searcher.getQueryProp("limit") * searcher.get("currentPage") - 1
        );
        query_api(searcher.get("query"));
      }
    };

    $scope.paginate_up = function() {
      if ($scope.numpages > $scope.page) {
        $scope.page = searcher.incrementCurrentPage();
        $scope.query.offset = $scope.query.limit * ($scope.page - 1);
        query_api($scope.query);
      }
    };

    $scope.page = searcher.get("currentPage");
    /*
    * End pagination
    */

    if (!Configs.hasOwnProperty("disableQuerySync")) {
      // Keep in sync the page location with the query object
      $scope.$watch(
        "query",
        function() {
          $location.search($scope.query);
        },
        true
      );
    }

    // Hierarchical keywords listeners
    PubSub.subscribe("select_h_keyword", function($event, element) {
      var data_filter = "keywords__slug__in";
      var query_entry = [];
      var value = element.href ? element.href : element.text;
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

    PubSub.subscribe("unselect_h_keyword", function($event, element) {
      var data_filter = "keywords__slug__in";
      var query_entry = [];
      var value = element.href ? element.href : element.text;
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
        delete $scope.query[data_filter];
      }
      query_api($scope.query);
    });

    /*
    * Add the selection behavior to the element, it adds/removes the 'active' class
    * and pushes/removes the value of the element from the query object
    */
    $scope.multiple_choice_listener = function($event) {
      var element = $($event.currentTarget);
      var query_entry = [];
      var data_filter = element.attr("data-filter");
      var value = element.attr("data-value");

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
      if (element.hasClass("active")) {
        // clear the active class from it
        element.removeClass("active");

        // Remove the entry from the correct query in scope

        query_entry.splice(query_entry.indexOf(value), 1);
      } else if (!element.hasClass("active")) {
        // if is not active then activate it
        // Add the entry in the correct query
        if (query_entry.indexOf(value) == -1) {
          query_entry.push(value);
        }
        element.addClass("active");
      }

      //save back the new query entry to the scope query
      $scope.query[data_filter] = query_entry;

      //if the entry is empty then delete the property from the query
      if (query_entry.length == 0) {
        delete $scope.query[data_filter];
      }
      query_api($scope.query);
    };

    $scope.single_choice_listener = function($event) {
      var element = $($event.currentTarget);
      var query_entry = [];
      var data_filter = element.attr("data-filter");
      var value = element.attr("data-value");
      // Type of data being displayed, use 'content' instead of 'all'
      $scope.dataValue = value == "all" ? "content" : value;

      // If the query object has the record then grab it
      if ($scope.query.hasOwnProperty(data_filter)) {
        query_entry = $scope.query[data_filter];
      }

      if (!element.hasClass("selected")) {
        // Add the entry in the correct query
        query_entry = value;

        // clear the active class from it
        element
          .parents("ul")
          .find("a")
          .removeClass("selected");

        element.addClass("selected");

        //save back the new query entry to the scope query
        $scope.query[data_filter] = query_entry;

        query_api($scope.query);
      }
    };

    /*
    * Region search management
    */
    var region_autocomplete = $("#region_search_input").yourlabsAutocomplete({
      url: AUTOCOMPLETE_URL_REGION,
      choiceSelector: "span",
      hideAfter: 200,
      minimumCharacters: 1,
      appendAutocomplete: $("#region_search_input"),
      placeholder: gettext("Enter your region here ...")
    });
    $("#region_search_input").bind("selectChoice", function(
      e,
      choice,
      region_autocomplete
    ) {
      if (choice[0].children[0] == undefined) {
        $("#region_search_input").val(choice[0].innerHTML);
        $("#region_search_btn").click();
      }
    });

    $("#region_search_btn").click(function() {
      $scope.query["regions__name__in"] = $("#region_search_input").val();
      query_api($scope.query);
    });

    $scope.feature_select = function($event) {
      var element = $(event.currentTarget);
      var article = $(element.parents("article")[0]);
      if (article.hasClass("resource_selected")) {
        element.html("Select");
        article.removeClass("resource_selected");
      } else {
        element.html("Deselect");
        article.addClass("resource_selected");
      }
    };

    /*
    * Date management
    */

    $scope.date_query = {
      date__gte: "",
      date__lte: ""
    };
    var init_date = true;
    $scope.$watch(
      "date_query",
      function() {
        if (
          $scope.date_query.date__gte != "" &&
          $scope.date_query.date__lte != ""
        ) {
          $scope.query["date__range"] =
            $scope.date_query.date__gte + "," + $scope.date_query.date__lte;
          delete $scope.query["date__gte"];
          delete $scope.query["date__lte"];
        } else if ($scope.date_query.date__gte != "") {
          $scope.query["date__gte"] = $scope.date_query.date__gte;
          delete $scope.query["date__range"];
          delete $scope.query["date__lte"];
        } else if ($scope.date_query.date__lte != "") {
          $scope.query["date__lte"] = $scope.date_query.date__lte;
          delete $scope.query["date__range"];
          delete $scope.query["date__gte"];
        } else {
          delete $scope.query["date__range"];
          delete $scope.query["date__gte"];
          delete $scope.query["date__lte"];
        }
        if (!init_date) {
          query_api($scope.query);
        } else {
          init_date = false;
        }
      },
      true
    );

    /*
    * Spatial search
    */
    if ($(".leaflet_map").length > 0) {
      angular.extend($scope, {
        layers: {
          baselayers: {
            stamen: {
              name: "OpenStreetMap Mapnik",
              type: "xyz",
              url: "//{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
              layerOptions: {
                subdomains: ["a", "b", "c"],
                attribution:
                  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
                continuousWorld: true
              }
            }
          }
        },
        map_center: {
          lat: 5.6,
          lng: 3.9,
          zoom: 0
        },
        defaults: {
          zoomControl: false
        }
      });

      var leafletData = $injector.get("leafletData"),
        map = leafletData.getMap("filter-map");

      map.then(function(map) {
        map.on("moveend", function() {
          $scope.query["extent"] = map.getBounds().toBBoxString();
          query_api($scope.query);
        });
      });

      var showMap = false;
      $("#_extent_filter").click(function(evt) {
        showMap = !showMap;
        if (showMap) {
          leafletData.getMap().then(function(map) {
            map.invalidateSize();
          });
        }
      });
    }
  });
})();
