/*
  Unselect all members of a list and select the target.
*/

export default ({ className = "selected", element = $() }) => {
  if (!element.hasClass(className)) {
    element
      .parents("ul")
      .find("a")
      .removeClass(className);
    element.addClass(className);
  }
};
