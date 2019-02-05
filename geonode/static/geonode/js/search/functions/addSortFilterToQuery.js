import modifyQuery from "app/search/functions/modifyQuery";
import getSortFilter from "app/search/functions/getSortFilter";

/*
  addSortFilterToQuery :: ({element: jQueryObject, query: queryObject}) =>
  queryObject
*/

export default ({
  element,
  query,
  singleValue = true,
  selectionClass = "selected"
}) => {
  const modifiedQuery = modifyQuery({
    value: element.attr("data-value"),
    selectionType: !element.hasClass(selectionClass) ? "select" : "unselect",
    query,
    filter: element.attr("data-filter"),
    singleValue
  });
  modifiedQuery.sortFilter = getSortFilter(element);
  return modifiedQuery;
};
