import searchHelpers from "app/search/helpers/searchHelpers";

function create() {
  const defaultState = {
    currentPage: 0,
    numberOfPages: 1,
    resultCount: 0,
    results: [],
    query: {
      limit: 1,
      offset: 1
    }
  };

  let state = { ...defaultState };

  const logError = prop => {
    // eslint-disable-next-line
    console.warn(`Search.${prop} does not exist.`);
  };

  const exists = (obj, prop) => Object.prototype.hasOwnProperty.call(obj, prop);
  const module = {
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
      if (!exists(state.query, prop)) {
        logError(`query.${prop}`);
        return false;
      }
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
    calculateNumberOfPages: (totalResults, limit) => {
      const n = Math.round(totalResults / limit + 0.49);
      return n === 0 ? 1 : n;
    },
    search: (url, params) =>
      new Promise(res => {
        searchHelpers.fetch(url, params).then(data => {
          module.setStateFromData(data);
          res(data);
        });
      }),
    setStateFromData(data) {
      module.set("results", data.objects);
      module.set("resultCount", parseInt(data.meta.total_count, 10));
    }
  };
  return module;
}

export default {
  create
};
