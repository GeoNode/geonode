function create() {
  const state = {
    currentPage: 0,
    numberOfPages: 1,
    resultCount: 0,
    results: []
  };

  return {
    inspect: () => state,
    get: prop => state[prop],
    set: (prop, val) => {
      if (!Object.prototype.hasOwnProperty.call(state, prop)) {
        // eslint-disable-next-line
        console.warn(`Search.${prop} does not exist.`);
        return false;
      }
      state[prop] = val;
      return state[prop];
    },
    resetNumberOfPages() {
      state.numberOfPages = 1;
    },
    calculateNumberOfPages: (totalCount, limit) =>
      Math.round(totalCount / limit + 0.49)
  };
}

export default {
  create
};
