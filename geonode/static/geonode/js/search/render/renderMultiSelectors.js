import elementExists from "app/helpers/elementExists";
import MultiSelector from "app/search/components/multiselectors/MultiSelector";
import MultiList from "app/search/components/multiselectors/MultiList";
import getMultiSelectorData from "app/search/components/multiselectors/getMultiSelectorData";
import MULTISELECT_FILTERS from "app/search/components/multiselectors/MULTISELECT_FILTERS";
import React from "react";
import ReactDOM from "react-dom";

const getObjById = (queue, id) => queue.filter(req => req.id === id)[0];

// Create a data model to instaniate filter selectors.
const getModel = (entry, aliasObject) => ({
  count: entry[aliasObject.count],
  content: entry[aliasObject.content],
  value: entry[aliasObject.value]
});

function render(multiSelectObjectArray) {
  MULTISELECT_FILTERS.map(filter => {
    // If the DOM element doesn't exist, don't attempt to render it.
    const elId = `${filter.elId || filter.id}MultiList`;
    if (!elementExists(elId)) return false;

    // Get the data to populate the multiselect filters.
    const multiSelectFilterData = getObjById(multiSelectObjectArray, filter.id)
      .data;

    // Build an array of filter selectors.
    const selectorModels = multiSelectFilterData
      .filter(entry => entry[filter.alias.count])
      .map((entry, i) => {
        const model = getModel(entry, filter.alias);
        model.filter = filter.filter;
        return model;
      });

    const selectors = selectorModels.map((model, i) => (
      <MultiSelector key={i} model={model} />
    ));

    // Render the multiselector list.
    ReactDOM.render(
      <MultiList selectors={selectors} name={filter.id} />,
      document.getElementById(`render_${filter.elId || filter.id}MultiList`)
    );
    return true;
  });
}

export default $scope => {
  getMultiSelectorData($scope).then(render);
};
