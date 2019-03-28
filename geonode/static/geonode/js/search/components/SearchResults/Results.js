import React from "react";
import Empty from "app/search/components/SearchResults/Empty";
import Listing from "app/search/components/SearchResults/Listing";
import PubSub from "app/utils/pubsub";

export default class Results extends React.Component {
  state = {
    results: []
  };
  constructor() {
    super();
    PubSub.subscribe("searchComplete", (event, searcher) => {
      if (!searcher.get) return;
      this.setState({
        results: searcher.get("results")
      });
    });
  }
  renderResultsOrEmpty = () => {
    if (!this.state.results.length) return <Empty />;
    return this.state.results.map((result, i) => {
      result.key = i;
      return <Listing key={i} result={result} />;
    });
  };
  render = () => (
    <div className="row resourcebase-snippet">
      {this.renderResultsOrEmpty()}
    </div>
  );
}
