/*
#########################################################################
#
# Copyright (C) 2019 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################
*/

import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { Tabs, Tab } from 'material-ui/Tabs';
import HoverPaper from '../../atoms/hover-paper';
import styles from './styles';
import actions from './actions';


const mapStateToProps = (state) => ({
  errorDetails: state.errorDetails.response,
  from: state.interval.from,
  to: state.interval.to,
});


@connect(mapStateToProps, actions)
class ErrorDetail extends React.Component {
  static propTypes = {
    errorDetails: PropTypes.object,
    errorId: PropTypes.number,
    get: PropTypes.func.isRequired,
  }

  componentWillMount() {
    this.props.get(this.props.errorId);
  }

  render() {
    const errorDetails = this.props.errorDetails;
    const result = {
      client: {},
    };
    if (errorDetails) {
      const date = new Date(errorDetails.created);
      const year = date.getFullYear();
      const month = `0${date.getMonth() + 1}`.slice(-2);
      const day = `0${date.getDate()}`.slice(-2);
      const hours = `0${date.getHours()}`.slice(-2);
      const minutes = `0${date.getMinutes()}`.slice(-2);
      const seconds = `0${date.getSeconds()}`.slice(-2);
      const formatedDate = `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
      result.date = `Date: ${formatedDate}`;
      result.service = `Service: ${errorDetails.service.name}`;
      result.errorType = `Type: ${errorDetails.error_type}`;
      result.errorData = errorDetails.error_data;
      if (errorDetails.request) {
        const request = errorDetails.request.request;
        const url = `${request.path}`;
        result.url = <span>URL: <a href={url}>{url}</a></span>;
        const response = errorDetails.request.response;
        result.errorCode = `Status code: ${response.status}`;
        if (errorDetails.request.client) {
          const client = errorDetails.request.client;
          result.client.ip = `IP: ${client.ip}`;
          result.client.userAgent = `Browser: ${client.user_agent}`;
          result.client.userAgentFamily = `Browser Family: ${client.user_agent_family}`;
        }
      }
    }
    return (
      <HoverPaper style={styles.content}>
        <div style={styles.header}>
          <h3 style={styles.title}>Error id: {this.props.errorId}</h3>
        </div>

        <Tabs>
          <Tab label="Metadata">
            <div style={styles.tab}>
              <div>{result.date}</div>
              <div>{result.service}</div>
              <div>{result.errorType}</div>
              <div>{result.errorCode}</div>
              <div>{result.url}</div>
            </div>
          </Tab>
          <Tab label="Client">
            <div style={styles.tab}>
              <div>{result.client.ip}</div>
              <div>{result.client.userAgent}</div>
              <div>{result.client.userAgentFamily}</div>
            </div>
          </Tab>
        </Tabs>

        <h3>Log</h3>
        <pre style={styles.log}>{result.errorData}</pre>
      </HoverPaper>
    );
  }
}


export default ErrorDetail;
