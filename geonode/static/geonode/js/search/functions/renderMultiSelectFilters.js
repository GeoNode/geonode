import elementExists from "app/helpers/elementExists";
import MultiSelector from "app/search/components/MultiSelector";
import MultiList from "app/search/components/MultiList";
import React from "react";
import ReactDOM from "react-dom";

const getRequestById = (queue, id) => queue.filter(req => req.id === id)[0];

// Create a data model to instaniate filter selectors.
const getModel = (entry, aliasObject) => ({
  count: entry[aliasObject.count],
  content: entry[aliasObject.content],
  value: entry[aliasObject.value]
});

export default (resolvedRequests, filters) => {
  filters.map(filter => {
    // If the DOM element doesn't exist, don't attempt to render it.
    const elId = `${filter.elId || filter.id}MultiList`;
    if (!elementExists(elId)) return false;

    // Get the data to populate the multiselect filters.
    const resolvedData = getRequestById(resolvedRequests, filter.id).data;

    // Build an array of filter selectors.
    const selectors = resolvedData
      .filter(entry => entry[filter.alias.count])
      .map((entry, i) => {
        const model = getModel(entry, filter.alias);
        return <MultiSelector key={i} filter={filter.filter} model={model} />;
      });

    // Render the multiselector list.
    ReactDOM.render(
      <MultiList selectors={selectors} name={filter.id} />,
      document.getElementById(`${filter.elId || filter.id}MultiList`)
    );
    return true;
  });
};
