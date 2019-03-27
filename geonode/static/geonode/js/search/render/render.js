import activateSidebarToggle from "app/search/functions/activateSidebarToggle";
import activateFilters from "app/search/functions/activateFilters";
import renderMultiSelectors from "app/search/render/renderMultiSelectors";
import renderPagination from "app/search/render/renderPagination";
import activateKeywordFilter from "app/search/functions/activateKeywordFilter";
import React from "react";
import ReactDOM from "react-dom";
import DateFilter from "app/search/components/DateFilter";
import SortFilter from "app/search/components/SortFilter";
import Results from "app/search/components/SearchResults/Results";
import Cart from "app/search/components/Cart";

export default $scope =>
  new Promise(res => {
    // Request the data needed to build query filters.

    ReactDOM.render(
      <DateFilter />,
      document.getElementById(`render_dateFilter`)
    );

    ReactDOM.render(
      <SortFilter />,
      document.getElementById(`render_sortFilter`)
    );

    ReactDOM.render(<Results />, document.getElementById(`render_results`));

    ReactDOM.render(<Cart />, document.getElementById(`render_cart`));

    activateKeywordFilter();
    renderMultiSelectors($scope);
    renderPagination();
    setTimeout(() => {
      activateSidebarToggle();
      activateFilters();
    }, 2000);
    res();
  });
