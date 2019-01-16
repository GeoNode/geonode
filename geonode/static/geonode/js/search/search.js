const search = {
  currentPage: 0,
  numberOfPages: 1,
  resultCount: 0,
  results: [],
  getResults() {
    return this.results;
  },
  setResults(results) {
    this.results = results;
  },
  getResultCount() {
    return this.resultCount;
  },
  setResultCount(num) {
    this.resultCount = num;
  },
  resetNumberOfPages() {
    this.numberOfPages = 1;
  },
  setNumberOfPages(num) {
    this.numberOfPages = num;
  },
  getNumberOfPages() {
    return this.numberOfPages;
  },
  calculateNumberOfPages: (totalCount, limit) =>
    Math.round(totalCount / limit + 0.49)
};

function create() {
  return search;
}

export default {
  create
};
