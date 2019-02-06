import locationUtils from "app/utils/locationUtils";
import queryFetch from "app/helpers/queryFetch";

/*
  A modified promise queue. Takes an array of objects containing an endpoint
  and query parameters, requests data based on these objects, and returns the
  data in an array matching the order of the query objects provided.
*/

const setInitialFiltersFromQuery = (data, urlQuery, filterParam) =>
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
  });

const buildRequestFromParam = ({
  endpoint,
  filterType,
  requestParam,
  filterParam,
  alias,
  customCallback
}) =>
  new Promise(res => {
    const cb = data => {
      if (locationUtils.paramExists(filterParam)) {
        data.objects = setInitialFiltersFromQuery(
          data.objects,
          locationUtils.getUrlParam(filterParam),
          alias
        );
      }
    };
    requestParam = requestParam || "title__icontains";
    const params =
      typeof filterType === "undefined" ? {} : { type: filterType };
    if (locationUtils.paramExists(requestParam)) {
      // eslint-disable-next-line
      params[requestParam] = locationUtils.getUrlParam(requestParam);
    }
    queryFetch(endpoint, { params }).then(data => {
      if (customCallback) customCallback(data);
      else cb(data);
      res(data.objects);
    });
  });

export default configs =>
  new Promise(res => {
    const promises = configs.map(cfg => buildRequestFromParam(cfg));
    Promise.all(promises).then(data => {
      res(data);
    });
  });
