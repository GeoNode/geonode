import React from "react";
import Empty from "app/search/components/SearchResults/Empty";

export default class Results extends React.Component {
  state = {
    results: []
  };
  renderResultsOrEmpty = () => {
    if (!this.state.results.length) return Empty;
    return "";
  };
  render = () => (
    <div className="row resourcebase-snippet">
      {this.renderResultsOrEmpty()}
    </div>
  );
}
