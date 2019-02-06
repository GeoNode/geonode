import elementExists from "app/search/functions/elementExists";
import MultiSelector from "app/search/components/MultiSelector";
import MultiList from "app/search/components/MultiList";
import React from "react";
import ReactDOM from "react-dom";

const getRequestById = (queue, id) => queue.filter(req => req.id === id)[0];

const fieldMaps = [
  {
    id: "owners",
    value: "username",
    filter: "owner__username__in",
    count: "count",
    content: "full_name"
  },
  {
    id: "categories",
    value: "identifier",
    count: "layers_count",
    content: "gn_description",
    filter: "category__identifier__in",
    elId: "layercategories"
  },
  {
    id: "categories",
    value: "identifier",
    count: "count",
    filter: "category__identifier__in",
    content: "gn_description"
  }
];

export default requestQueue => {
  fieldMaps.map(fieldMap => {
    const elId = `${fieldMap.elId || fieldMap.id}MultiList`;
    if (!elementExists(elId)) return false;
    const data = getRequestById(requestQueue, fieldMap.id).data;
    const list = data.filter(entry => entry[fieldMap.count]).map((entry, i) => {
      const model = {
        name: entry[fieldMap.name],
        count: entry[fieldMap.count],
        content: entry[fieldMap.content],
        value: entry[fieldMap.value]
      };
      return <MultiSelector key={i} filter={fieldMap.filter} model={model} />;
    });
    ReactDOM.render(
      <MultiList selectors={list} name={fieldMap.id} />,
      document.getElementById(`${fieldMap.elId || fieldMap.id}MultiList`)
    );
    return true;
  });
};
