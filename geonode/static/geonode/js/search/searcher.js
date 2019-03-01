import Search from "app/search/components/Search";

/*
  An instance of the Search factory function that is used to store all
  state related to Geonode search.
*/
const searcher = Search({
  searchURL: "/api/base/"
});
export default searcher;
