import locationUtils from "app/utils/locationUtils";

/*
  Activates sort & type filters if they exist in the URL
  query string.
*/

export default () => {
  if (locationUtils.paramExists("type__in")) {
    const types = locationUtils.getUrlParam("type__in");
    if (types instanceof Array) {
      for (let i = 0; i < types.length; i += 1) {
        $("body")
          .find(`[data-filter='type__in'][data-value=${types[i]}]`)
          .addClass("active");
      }
    } else {
      $("body")
        .find(`[data-filter='type__in'][data-value=${types}]`)
        .addClass("active");
    }
  }

  if (locationUtils.paramExists("order_by")) {
    const sort = locationUtils.getUrlParam("order_by");
    $("body")
      .find("[data-filter='order_by']")
      .removeClass("selected");
    $("body")
      .find(`[data-filter='order_by'][data-value=${sort}]`)
      .addClass("selected");
  }
};
