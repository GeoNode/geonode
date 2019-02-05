/*
  Add a filter to a provided query object if the selectionType is "select",
  remove it if the selectionType is "unselect" and return the modified
  query object.
*/

export default ({
  value = "val",
  selectionType = "select",
  query = {},
  filter = "keywords__slug__in",
  singleValue = false,
  sortFilter = null
}) => {
  const dataFilter = filter;
  let queryEntry = [];

  // If the filter only accepts one value, begin with an empty array.
  if (singleValue) {
    query[dataFilter] = queryEntry;
  }

  // Check if filter property already exists on the query object.
  const hasProp = Object.prototype.hasOwnProperty.call(query, dataFilter);
  if (hasProp) {
    if (query[dataFilter] instanceof Array) {
      queryEntry = query[dataFilter];
    } else {
      queryEntry.push(query[dataFilter]);
    }
  }

  // Add or remove query depending on selection type.
  if (selectionType === "unselect") {
    queryEntry.splice(queryEntry.indexOf(value), 1);
  } else if (selectionType === "select" && queryEntry.indexOf(value) === -1) {
    queryEntry.push(value);
  }

  if (queryEntry.length === 0) {
    delete query[dataFilter];
  }

  if (selectionType === "select") {
    query[dataFilter] = queryEntry;
  }

  if (sortFilter) {
    query.sortFilter = sortFilter;
  }

  // return the modified query
  return query;
};
