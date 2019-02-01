/*
  getSortFilter :: (jQueryObject) => boolean;
*/

export default $element => {
  const value = $element.attr("data-value");
  return value === "all" ? "content" : value;
};
