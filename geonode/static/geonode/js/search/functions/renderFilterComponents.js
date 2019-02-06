import getRequestQueue from "app/search/functions/getRequestQueue";
import requestMultiple from "app/search/functions/requestMultiple";
import activateSidebarToggle from "app/search/functions/activateSidebarToggle";
import activateFilters from "app/search/functions/activateFilters";
import renderMultiSelectFilters from "app/search/functions/renderMultiSelectFilters";
import activateKeywordFilter from "app/search/functions/activateKeywordFilter";
import MULTISELECT_FILTERS from "app/search/constants/MULTISELECT_FILTERS";

export default $scope =>
  new Promise(res => {
    // Request the data needed to build query filters.
    let requestQueue = getRequestQueue();
    activateKeywordFilter();
    requestMultiple(requestQueue).then(reqArray => {
      requestQueue = requestQueue.map((req, i) => {
        req.data = reqArray[i];
        $scope[requestQueue[i].id] = reqArray[i];
        return req;
      });
      renderMultiSelectFilters(requestQueue, MULTISELECT_FILTERS);
      activateFilters();
      activateSidebarToggle();
      res();
    });
  });
