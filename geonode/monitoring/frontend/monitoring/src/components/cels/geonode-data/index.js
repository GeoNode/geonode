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
import { getResponseData } from '../../../utils';
import AverageResponseTime from '../../molecules/average-response-time';
import MaxResponseTime from '../../molecules/max-response-time';
import TotalRequests from '../../molecules/total-requests';
import styles from './styles';
import actions from './actions';


const mapStateToProps = (state) => ({
  interval: state.interval.interval,
  response: state.geonodeAverageResponse.response,
  timestamp: state.interval.timestamp,
});


@connect(mapStateToProps, actions)
class GeonodeData extends React.Component {
  static propTypes = {
    get: PropTypes.func.isRequired,
    interval: PropTypes.number,
    reset: PropTypes.func.isRequired,
    response: PropTypes.object,
    timestamp: PropTypes.instanceOf(Date),
  }

  constructor(props) {
    super(props);
    this.get = (interval = this.props.interval) => {
      this.props.get(interval);
    };
  }

  componentWillMount() {
    this.get();
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps) {
      if (nextProps.timestamp && nextProps.timestamp !== this.props.timestamp) {
        this.get(nextProps.interval);
      }
    }
  }

  componentWillUnmount() {
    this.props.reset();
  }

  render() {
    let averageResponseTime = 0;
    let maxResponseTime = 0;
    let totalRequests = 0;
    [
      averageResponseTime,
      maxResponseTime,
      totalRequests,
    ] = getResponseData(this.props.response);
    return (
      <div style={styles.content}>
        <h5>Geonode Data Overview</h5>
        <div style={styles.geonode}>
          <AverageResponseTime time={averageResponseTime} />
          <MaxResponseTime time={maxResponseTime} />
        </div>
        <TotalRequests requests={totalRequests} />
      </div>
    );
  }
}


export default GeonodeData;
