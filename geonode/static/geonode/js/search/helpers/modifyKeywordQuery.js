/*
  `modifyKeywordQuery` adds a keyword query to a provided query object if
  the selectionType is "select" and removes it if the selectionType is
  "unselect" and then returns the modified keyword object.
*/

export default ({ value, selectionType, query, filter }) => {
  const dataFilter = filter || "keywords__slug__in";
  let queryEntry = [];
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

  // return the modified query
  return query;
};
