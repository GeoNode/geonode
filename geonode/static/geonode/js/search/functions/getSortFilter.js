/*
  Get sort filter type from DOM element.
*/

export default $element => {
  const value = $element.attr("data-value");
  return value === "all" ? "content" : value;
};
