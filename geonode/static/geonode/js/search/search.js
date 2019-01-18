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
        var esc = encodeURIComponent;
        var query = Object.keys(params)
          .map(k => `${esc(k)}=${esc(params[k])}`)
          .join("&");
        fetch(`${url}?${query}`)
          .then(r => r.json())
          .then(data => {
            api.setStateFromData(data);
            res(data);
          });
      }),
    setStateFromData(data) {
      api.set("results", data.objects);
      api.set("resultCount", parseInt(data.meta.total_count, 10));
    }
  };
  return api;
}

export default {
  create
};
