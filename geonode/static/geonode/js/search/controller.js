import searcher from "app/search/searcher";
import PubSub from "app/utils/pubsub";
import Map from "app/search/components/Map";
import TextSearchForm from "app/search/components/TextSearchForm";
import angularShim from "app/utils/angularShim";
import locationUtils from "app/utils/locationUtils";
import modifyQuery from "app/search/functions/modifyQuery";
import toggleList from "app/helpers/toggleList";
import addSortFilterToQuery from "app/search/functions/addSortFilterToQuery";
import setDefaultSearchState from "app/search/functions/setDefaultSearchState";
import render from "app/search/render/render";

export default (() => {
  /*
    `syncScope` is used as a shim while AngularJS is being phased out of
    the project. The `Search` instance is the single source of truth for
    search state, and the AngularJS $scope object is synced to the instance's
    data model after the query is executed in order to update the view.
  */

  const syncAngular = angularShim.syncScope([
    ["page", "currentPage"],
    ["query", "query"],
    ["results", "results"],
    ["total_counts", "resultCount"],
    ["numpages", "numberOfPages"],
    ["text_query", "queryValue"],
    ["dataValue", "sortFilter"]
  ]);

  const syncView = ($scope, search) => {
    syncAngular($scope, search);
    PubSub.publish("syncView", search.inspect());
  };

  const module = angular.module("geonode_main_search", []);

  /*
  * Main search controller
  * Load data from api and defines the multiple and single choice handlers
  * Syncs the browser url with the selections
  */
  module.controller("geonode_search_controller", $scope => {
    // Create a search instance to track search state
    setDefaultSearchState(searcher);

    // Add extent map
    Map({
      id: "filter-map"
    });

    // Add omni search form
    const textSearchInstance = TextSearchForm({
      url: window.AUTOCOMPLETE_URL_RESOURCEBASE,
      id: "text_search"
    });

    // Add region search form
    TextSearchForm({
      url: window.AUTOCOMPLETE_URL_REGION,
      id: "region_search"
    });

    // Get data from apis and make them available to the page
    function queryApi(params = searcher.get("query")) {
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
        PubSub.publish("searchComplete", searcher);
        syncView($scope, searcher);
      });
    }

    // Execute initial query
    queryApi();

    // Render React components
    render($scope).then(() => {
      syncView($scope, searcher);
    });

    // Handle omni search
    PubSub.subscribe("searchSubmitted", (event, search) => {
      if (search.id !== "text_search") return;
      let queryKey;
      if (search.url === "/autocomplete/ProfileAutocomplete/") {
        // a user profile has no title; if search was triggered from
        // the /people page, filter by username instead
        queryKey = "username__icontains";
      } else {
        // eslint-disable-next-line
        queryKey =
          textSearchInstance.getForm().data("query-key") || "title__icontains";
      }
      const searchVal = textSearchInstance.getFormVal();
      searcher.setQueryProp(queryKey, searchVal);
      queryApi(searcher.get("query"));
    });

    // Handle region search
    PubSub.subscribe("searchSubmitted", (event, search) => {
      if (search.id !== "region_search") return;
      // eslint-disable-next-line
      $scope.query["regions__name__in"] = search.value;
      queryApi($scope.query);
    });

    // Handle pagination
    PubSub.subscribe("paginate", () => {
      queryApi();
    });

    // Handle extent map interaction
    PubSub.subscribe("mapMove", (event, extent) => {
      searcher.setQueryProp("extent", extent);
      queryApi(searcher.get("query"));
    });

    // Handle multiselect button click (owners, categories, types)
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

    // Handle date range change
    PubSub.subscribe("dateRangeUpdated", (event, modifiedQuery) => {
      searcher.set("query", modifiedQuery);
      queryApi(searcher.get("query"));
    });

    // Control what happens when the total results change
    $scope.$watch("total_counts", () => {
      searcher.handleResultChange();
      syncView($scope, searcher);
    });

    const updateKWQuery = (element, selectionType) => {
      const updatedQuery = modifyQuery({
        value: element.href ? element.href : element.text,
        selectionType,
        query: searcher.get("query")
      });
      searcher.set("query", updatedQuery);
      queryApi();
    };

    PubSub.subscribe("select_h_keyword", ($event, element) => {
      updateKWQuery(element, "select");
    });

    PubSub.subscribe("unselect_h_keyword", ($event, element) => {
      updateKWQuery(element, "unselect");
    });

    PubSub.subscribe("updateNumberOfPages", () => {
      queryApi();
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

    $("[data-filter*='order_by']").on("click", $event => {
      const $element = $($event.toElement);
      const value = $element.attr("data-value");
      const dataValue = value === "all" ? "content" : value;
      searcher.setQueryProp("dataValue", dataValue);
      searcher.set("sortFilter", dataValue);
      const updatedQuery = addSortFilterToQuery({
        element: $element,
        query: searcher.get("query")
      });
      searcher.set("query", updatedQuery);
      syncView($scope, searcher);
      if (!$element.hasClass("selected")) {
        toggleList({ element: $element });
        queryApi();
      }
    });
  });
})();
