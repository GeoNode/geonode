import React from "react";
import searcher from "app/search/searcher";
import PubSub from "app/utils/pubsub";

export default class DateFilter extends React.Component {
  constructor() {
    super();
    this.state = {
      startDate: "",
      endDate: ""
    };
  }
  handleStartDateChange = event => {
    this.setState({ startDate: event.target.value });
    this.updateQuery();
  };
  handleEndDateChange = event => {
    this.setState({ endDate: event.target.value });
    this.updateQuery();
  };
  updateQuery = () => {
    let initDate = true;
    const query = searcher.get("query");
    if (this.state.startDate !== "" && this.state.endDate !== "") {
      query["date__range"] = `${this.state.startDate}, ${this.state.endDate}`;
      delete query["date__gte"];
      delete query["date__lte"];
    } else if (this.state.startDate !== "") {
      query["date__gte"] = this.state.startDate;
      delete query["date__range"];
      delete query["date__lte"];
    } else if (this.state.endDate !== "") {
      query["date__lte"] = this.state.endDate;
      delete query["date__range"];
      delete query["date__gte"];
    } else {
      delete query["date__range"];
      delete query["date__gte"];
      delete query["date__lte"];
    }
    if (initDate) {
      PubSub.publish("dateRangeUpdated", query);
    } else {
      initDate = false;
    }
  };
  render = () => (
    <div>
      <h4>
        <a href="#" className="toggle toggle-nav">
          <i className="fa fa-chevron-right" />
          {window.gettext("Date")}
        </a>
      </h4>
      <ul className="nav closed" id="date_start">
        <label>{window.gettext("Date begins after:")}</label>
        <li>
          <input
            data-date-format="YYYY-MM-DD"
            type="text"
            className="datepicker"
            placeholder={window.gettext("yyyy-mm-dd")}
            onChange={this.handleStartDateChange}
            onBlur={this.handleStartDateChange}
          />
        </li>
      </ul>
      <ul className="nav closed" id="date_end">
        <label>{window.gettext("Date ends before:")}</label>
        <li>
          <input
            data-date-format="YYYY-MM-DD"
            type="text"
            className="datepicker"
            placeholder={window.gettext("yyyy-mm-dd")}
            onChange={this.handleEndDateChange}
            onBlur={this.handleEndDateChange}
          />
        </li>
      </ul>
    </div>
  );
}
