export default ($element, className) =>
  $element.hasClass(className)
    ? $element.removeClass(className)
    : $element.addClass(className);
