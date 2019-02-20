import activateSidebarToggle from "app/search/functions/activateSidebarToggle";
import activateFilters from "app/search/functions/activateFilters";
import renderMultiSelectors from "app/search/render/renderMultiSelectors";
import renderPagination from "app/search/render/renderPagination";
import activateKeywordFilter from "app/search/functions/activateKeywordFilter";

export default $scope =>
  new Promise(res => {
    // Request the data needed to build query filters.
    activateKeywordFilter();
    renderMultiSelectors($scope);
    renderPagination();
    setTimeout(() => {
      activateSidebarToggle();
      activateFilters();
    }, 2000);
    res();
  });
