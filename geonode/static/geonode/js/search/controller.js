import Search from "app/search/components/Search";
import PubSub from "app/utils/pubsub";
import TextSearchForm from "app/search/components/TextSearchForm";
import angularShim from "app/utils/angularShim";
import locationUtils from "app/utils/locationUtils";
import modifyQuery from "app/search/functions/modifyQuery";
import renderFilterComponents from "app/search/functions/renderFilterComponents";

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

  /*
  * Main search controller
  * Load data from api and defines the multiple and single choice handlers
  * Syncs the browser url with the selections
  */
  module.controller(
    "geonode_search_controller",
    ($injector, $scope, $location, Configs) => {
      /*
      * Load categories and keywords if the filter is available in the page
      * and set active class if needed
      */

      renderFilterComponents($scope).then(() => {
        syncScope($scope, searcher);
      });

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

          console.log("!!!!!QUERY", searcher.get("query"));

          queryValue.replace(/\+/g, " ");
          searcher.set("queryValue", queryValue);
          syncScope($scope, searcher);
        });
      }
      queryApi(searcher.get("query"));

      PubSub.subscribe("searchSubmitted", (event, search) => {
        if (search.id !== "text_search") return;
        PubSub.publish("searchSubmitted", search.id);
        let queryKey;
        if (search.url === "/autocomplete/ProfileAutocomplete/") {
          // a user profile has no title; if search was triggered from
          // the /people page, filter by username instead
          queryKey = "username__icontains";
        } else {
          // eslint-disable-next-line
          console.log("search key", textSearchInstance.getForm().data());
          queryKey =
            textSearchInstance.getForm().data("query-key") ||
            "title__icontains";
        }
        const searchVal = textSearchInstance.getFormVal();
        searcher.setQueryProp(queryKey, searchVal);
        queryApi(searcher.get("query"));
      });

      TextSearchForm({
        url: window.AUTOCOMPLETE_URL_REGION,
        id: "region_search"
      });

      PubSub.subscribe("searchSubmitted", (event, search) => {
        if (search.id !== "region_search") return;
        // eslint-disable-next-line
        $scope.query["regions__name__in"] = search.value;
        queryApi($scope.query);
      });

      PubSub.subscribe("paginateUp", queryApi);
      PubSub.subscribe("paginateDown", queryApi);

      // Handle multiselection filter click.
      PubSub.subscribe("multiSelectClicked", (event, data) => {
        const modifiedQuery = modifyQuery({
          value: data.value,
          selectionType: data.selectionType,
          query: searcher.get("query"),
          filter: data.filter,
          singleValue: false
        });
        searcher.set("query", modifiedQuery);
        queryApi(searcher.get("query"));
      });

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

      $scope.feature_select = $event => {
        const element = $($event.currentTarget);
        const article = $(element.parents("article")[0]);
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
      let initDate = true;
      $scope.$watch(
        "date_query",
        () => {
          if (
            $scope.date_query.date__gte !== "" &&
            $scope.date_query.date__lte !== ""
          ) {
            $scope.query["date__range"] = `${$scope.date_query
              .date__gte}, ${$scope.date_query.date__lte}`;
            delete $scope.query["date__gte"];
            delete $scope.query["date__lte"];
          } else if ($scope.date_query.date__gte !== "") {
            $scope.query["date__gte"] = $scope.date_query.date__gte;
            delete $scope.query["date__range"];
            delete $scope.query["date__lte"];
          } else if ($scope.date_query.date__lte !== "") {
            $scope.query["date__lte"] = $scope.date_query.date__lte;
            delete $scope.query["date__range"];
            delete $scope.query["date__gte"];
          } else {
            delete $scope.query["date__range"];
            delete $scope.query["date__gte"];
            delete $scope.query["date__lte"];
          }
          if (!initDate) {
            queryApi($scope.query);
          } else {
            initDate = false;
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
