import queryFetch from "app/helpers/queryFetch";
import PubSub from "pubsub-js";

const Search = ({ searchURL = "/api/base/" } = {}) => {
  const defaultState = {
    currentPage: 0,
    searchURL,
    numberOfPages: 1,
    resultCount: 0,
    results: [],
    sortFilter: "-date",
    queryValue: "",
    query: {
      limit: 0,
      extent: "",
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
    paginateUp: () => {
      if (api.get("numberOfPages") > api.get("currentPage")) {
        api.incrementCurrentPage();
        const offset = api.getQueryProp("limit") * (api.get("currentPage") - 1);
        api.setQueryProp("offset", offset);
        PubSub.publish("paginate");
      }
    },
    paginateDown: () => {
      if (api.get("currentPage") > 1) {
        api.decrementCurrentPage();
        api.setQueryProp(
          "offset",
          api.getQueryProp("limit") * api.get("currentPage") - 1
        );
        PubSub.publish("paginate");
      }
    },
    search: (query = api.get("query")) =>
      new Promise(res => {
        queryFetch(api.get("searchURL"), query).then(data => {
          api.setStateFromData(data);
          PubSub.publish("searchComplete", data);
          res(data);
        });
      }),
    setStateFromData(data) {
      api.set("results", data.objects);
      if (data.meta)
        api.set("resultCount", parseInt(data.meta.total_count, 10));
    },
    handleResultChange() {
      const numpages = api.calculateNumberOfPages(
        api.get("resultCount"),
        api.getQueryProp("limit")
      );
      api.set("numberOfPages", numpages);
      // In case the user is viewing a page > 1 and a
      // subsequent query returns less pages, then
      // reset the page to one and search again.
      if (api.get("numberOfPages") < api.get("currentPage")) {
        api.set("currentPage", 1);
        api.setQueryProp("offset", 0);
        PubSub.publish("updateNumberOfPages");
      }

      // In case of no results, the number of pages is one.
      if (api.get("numberOfPages") === 0) {
        api.set("numberOfPages", 1);
      }
    }
  };
  return api;
};

export default Search;
