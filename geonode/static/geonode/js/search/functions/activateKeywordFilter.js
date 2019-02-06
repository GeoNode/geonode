import SelectionTree from "app/search/components/SelectionTree";
import queryFetch from "app/helpers/queryFetch";

export default () => {
  const params =
    typeof FILTER_TYPE === "undefined" ? {} : { type: window.FILTER_TYPE };
  queryFetch(window.H_KEYWORDS_ENDPOINT, { params }).then(data => {
    SelectionTree({
      id: "treeview",
      data,
      eventId: "h_keyword"
    });
  });
};
