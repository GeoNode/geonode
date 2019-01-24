import locationUtils from "app/utils/locationUtils";

const module = {
  buildRequestFromParamQueue: configs =>
    new Promise(res => {
      const promises = configs.map(cfg => module.buildRequestFromParam(cfg));
      Promise.all(promises).then(data => {
        res(data);
      });
    }),

  buildRequestFromParam: ({
    endpoint,
    filterType,
    requestParam,
    filterParam,
    alias
  }) =>
    new Promise(res => {
      requestParam = requestParam || "title__icontains";
      const params =
        typeof filterType === "undefined" ? {} : { type: filterType };
      if (locationUtils.paramExists(requestParam)) {
        // eslint-disable-next-line
        params[requestParam] = locationUtils.getUrlParam(requestParam);
      }
      module.fetch(endpoint, { params }).then(data => {
        if (locationUtils.paramExists(filterParam)) {
          data.objects = module.setInitialFiltersFromQuery(
            data.objects,
            locationUtils.getUrlParam(filterParam),
            alias
          );
        }
        res(data.objects);
      });
    }),
  fetch: (url, params) =>
    new Promise(res => {
      const esc = encodeURIComponent;
      const query = Object.keys(params)
        .map(k => `${esc(k)}=${esc(params[k])}`)
        .join("&");
      fetch(`${url}?${query}`)
        .then(r => r.json())
        .then(data => {
          res(data);
        });
    }),
  setInitialFiltersFromQuery: (data, urlQuery, filterParam) =>
    data.map(datum => {
      if (
        urlQuery === datum[filterParam] ||
        urlQuery.indexOf(datum[filterParam]) !== -1
      ) {
        datum.active = "active";
      } else {
        datum.active = "";
      }
      return datum;
    })
};

export default module;
