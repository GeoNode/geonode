import locationUtils from "app/utils/locationUtils";

export default searchInstance => {
  searchInstance.set("query", locationUtils.getUrlParams());
  searchInstance.setQueryProp(
    "limit",
    searchInstance.getQueryProp("limit") || window.CLIENT_RESULTS_LIMIT
  );
  searchInstance.setQueryProp(
    "offset",
    searchInstance.getQueryProp("offset") || 0
  );
  searchInstance.set(
    "currentPage",
    Math.round(
      searchInstance.getQueryProp("offset") /
        searchInstance.getQueryProp("limit") +
        1
    )
  );
};
