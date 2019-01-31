import Search from "app/search/components/Search";
import PubSub from "app/utils/pubsub";
import SelectionTree from "app/search/components/SelectionTree";
import TextSearchForm from "app/search/components/TextSearchForm";
import angularShim from "app/utils/angularShim";
import locationUtils from "app/utils/locationUtils";
import modifyQuery from "app/search/functions/modifyQuery";
import getSortFilter from "app/search/functions/getSortFilter";
import queryFetch from "app/search/functions/queryFetch";
import buildRequestQueue from "app/search/functions/buildRequestQueue";
import activateFilters from "app/search/functions/activateFilters";
import toggleList from "app/search/functions/toggleList";

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
    ["text_query", "queryValue"],
    ["dataValue", "sortFilter"]
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

  module.loadHKeywords = () => {
    const params =
      typeof FILTER_TYPE === "undefined" ? {} : { type: window.FILTER_TYPE };
    queryFetch(window.H_KEYWORDS_ENDPOINT, { params }).then(data => {
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
  module.run($rootScope => {
    /*
    * Load categories and keywords if the filter is available in the page
    * and set active class if needed
    */

    const requestQueue = [
      {
        id: "categories",
        endpoint: window.CATEGORIES_ENDPOINT,
        requestParam: "title__icontains",
        filterParam: "category__identifier__in",
        alias: "identifier"
      },
      {
        id: "groupcategories",
        endpoint: window.GROUP_CATEGORIES_ENDPOINT,
        requestParam: "name__icontains",
        filterParam: "slug",
        alias: "identifier"
      },
      {
        id: "regions",
        endpoint: window.REGIONS_ENDPOINT,
        requestParam: "title__icontains",
        filterParam: "regions__name__in",
        alias: "name"
      },
      {
        id: "owners",
        endpoint: window.OWNERS_ENDPOINT,
        requestParam: "title__icontains",
        filterParam: "owner__username__in",
        alias: "identifier"
      },
      {
        id: "tkeywords",
        endpoint: window.T_KEYWORDS_ENDPOINT,
        requestParam: "title__icontains",
        filterParam: "tkeywords__id__in",
        alias: "id"
      },
      {
        id: "tkeywords",
        endpoint: window.H_KEYWORDS_ENDPOINT,
        requestParam: "title__icontains",
        filterParam: "tkeywords__id__in",
        alias: "id"
      }
      // Only make the request if a page element possessing the id exists
    ].filter(req => $(`#${req.id}`).length > 0);

    module.loadHKeywords();

    buildRequestQueue(requestQueue).then(data => {
      for (let i = 0; i < requestQueue.length; i += 1) {
        $rootScope[requestQueue[i].id] = data[i];
      }
    });

    activateFilters();
  });

  /*
  * Main search controller
  * Load data from api and defines the multiple and single choice handlers
  * Syncs the browser url with the selections
  */
  module.controller(
    "geonode_search_controller",
    ($injector, $scope, $location, Configs) => {
      searcher.set("query", locationUtils.getUrlParams());
      searcher.setQueryProp(
        "limit",
        5
        // !DJA HACK @TODO: searcher.getQueryProp("limit") || CLIENT_RESULTS_LIMIT
      );
      searcher.setQueryProp("offset", searcher.getQueryProp("offset") || 0);
      searcher.set(
        "currentPage",
        Math.round(
          searcher.getQueryProp("offset") / searcher.getQueryProp("limit") + 1
        )
      );

      const textSearchInstance = TextSearchForm({
        url: window.AUTOCOMPLETE_URL_RESOURCEBASE,
        id: "text_search"
      });

      // Get data from apis and make them available to the page
      function queryApi(params) {
        searcher.search(params).then(data => {
          setTimeout(() => {
            $('[ng-controller="CartList"] [data-toggle="tooltip"]').tooltip();
          });
          const formValue = textSearchInstance.getFormVal();
          const paramExists = locationUtils.paramExists("title__icontains");
          const param = locationUtils.getUrlParam("title__icontains");
          let queryValue = null;
          if (formValue) queryValue = formValue;
          else if (paramExists) queryValue = param;
          else queryValue = "";

          queryValue.replace(/\+/g, " ");
          searcher.set("queryValue", queryValue);
          syncScope($scope, searcher);
        });
      }
      queryApi(searcher.get("query"));

      /*
        Text search management
      */

      PubSub.subscribe("textSearchClick", (event, data) => {
        searcher.setQueryProp(data.key, data.val);
        queryApi(searcher.get("query"));
      });

      /*
        Pagination
      */
      // Control what happens when the total results change
      const handleResultChange = () => {
        const numpages = searcher.calculateNumberOfPages(
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
          queryApi(searcher.get("query"));
        }

        // In case of no results, the number of pages is one.
        if (searcher.get("numberOfPages") === 0) {
          searcher.set("numberOfPages", 1);
        }
        syncScope($scope, searcher);
      };

      $scope.$watch("total_counts", handleResultChange);

      $scope.paginate_down = searcher.paginateDown;

      $scope.paginate_up = searcher.paginateUp;

      $scope.page = searcher.get("currentPage");
      /*
    * End pagination
    */

      if (!Configs.hasOwnProperty("disableQuerySync")) {
        // Keep in sync the page location with the query object
        $scope.$watch(
          "query",
          () => {
            $location.search($scope.query);
          },
          true
        );
      }

      const updateKWQuery = (element, selectionType) => {
        const updatedQuery = modifyQuery({
          value: element.href ? element.href : element.text,
          selectionType,
          query: searcher.get("query")
        });
        searcher.set("query", updatedQuery);
        queryApi();
      };

      // Hierarchical keywords listeners
      PubSub.subscribe("select_h_keyword", ($event, element) => {
        updateKWQuery(element, "select");
      });

      PubSub.subscribe("unselect_h_keyword", ($event, element) => {
        updateKWQuery(element, "unselect");
      });

      /*
    * Add the selection behavior to the element, it adds/removes the 'active' class
    * and pushes/removes the value of the element from the query object
    */
      $scope.multiple_choice_listener = $event => {
        var element = $($event.currentTarget);
        var queryEntry = [];
        var dataFilter = element.attr("data-filter");
        var value = element.attr("data-value");

        // If the query object has the record then grab it
        if ($scope.query.hasOwnProperty(dataFilter)) {
          // When in the location are passed two filters of the same
          // type then they are put in an array otherwise is a single string
          if ($scope.query[dataFilter] instanceof Array) {
            queryEntry = $scope.query[dataFilter];
          } else {
            queryEntry.push($scope.query[dataFilter]);
          }
        }

        // If the element is active active then deactivate it
        if (element.hasClass("active")) {
          // clear the active class from it
          element.removeClass("active");

          // Remove the entry from the correct query in scope

          queryEntry.splice(queryEntry.indexOf(value), 1);
        } else if (!element.hasClass("active")) {
          // if is not active then activate it
          // Add the entry in the correct query
          if (queryEntry.indexOf(value) === -1) {
            queryEntry.push(value);
          }
          element.addClass("active");
        }

        // save back the new query entry to the scope query
        $scope.query[dataFilter] = queryEntry;

        // if the entry is empty then delete the property from the query
        if (queryEntry.length == 0) {
          delete $scope.query[dataFilter];
        }
        queryApi($scope.query);
      };

      $scope.single_choice_listener = $event => {
        const element = $($event.currentTarget);
        const updatedQuery = modifyQuery({
          value: element.attr("data-value"),
          selectionType: !element.hasClass("selected") ? "select" : "unselect",
          query: searcher.get("query"),
          filter: element.attr("data-filter"),
          singleValue: true
        });
        searcher.set("query", updatedQuery);
        searcher.set("sortFilter", getSortFilter(element));
        syncScope($scope, searcher);

        toggleList({ element });
        if (!element.hasClass("selected")) {
          queryApi();
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
        queryApi($scope.query);
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
            queryApi($scope.query);
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
            queryApi($scope.query);
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
    }
  );
})();
