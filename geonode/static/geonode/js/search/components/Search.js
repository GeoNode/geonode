import searchHelpers from "app/search/helpers/searchHelpers";
import PubSub from "pubsub-js";

const Search = ({ searchURL = "/api/base/" } = {}) => {
  const defaultState = {
    currentPage: 0,
    searchURL,
    numberOfPages: 1,
    resultCount: 0,
    results: [],
    queryValue: "",
    query: {
      limit: 1,
      offset: 0
    }
  };

  let state = { ...defaultState };

  const logError = prop => {
    // eslint-disable-next-line
    console.warn(`Search.${prop} does not exist.`);
  };

  const exists = (obj, prop) => Object.prototype.hasOwnProperty.call(obj, prop);
  const api = {
    inspect: () => state,
    get: prop => state[prop],
    set: (prop, val) => {
      if (!exists(state, prop)) {
        logError(prop);
        return false;
      }
      state[prop] = val;
      return state[prop];
    },
    setQueryProp: (prop, val) => {
      state.query[prop] = val;
      return state.query[prop];
    },
    getQueryProp: prop => state.query[prop],
    resetNumberOfPages() {
      state.numberOfPages = 1;
    },
    reset() {
      state = { ...defaultState };
    },
    getCurrentPage: () => state.currentPage,
    incrementCurrentPage: () => {
      state.currentPage += 1;
      return state.currentPage;
    },
    decrementCurrentPage: () => {
      state.currentPage -= 1;
      return state.currentPage;
    },
    calculateNumberOfPages: (totalResults, limit) => {
      const n = Math.round(totalResults / limit + 0.49);
      return n === 0 ? 1 : n;
    },
    paginateDown: () => {
      if (api.get("currentPage") > 1) {
        api.decrementCurrentPage();
        api.setQueryProp(
          "offset",
          api.getQueryProp("limit") * api.get("currentPage") - 1
        );
        api.search();
      }
    },
    search: query =>
      new Promise(res => {
        searchHelpers.fetch(api.get("searchURL"), query).then(data => {
          api.setStateFromData(data);
          PubSub.publish("searchComplete", data);
          res(data);
        });
      }),
    setStateFromData(data) {
      api.set("results", data.objects);
      api.set("resultCount", parseInt(data.meta.total_count, 10));
    }
  };
  return api;
};

export default Search;
