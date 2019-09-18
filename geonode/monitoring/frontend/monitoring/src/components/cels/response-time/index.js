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
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import styles from './styles';


class ResponseTime extends React.Component {
  static propTypes = {
    average: PropTypes.number.isRequired,
    data: PropTypes.array.isRequired,
    max: PropTypes.number.isRequired,
  }

  render() {
    let avgResponse = 0;
    let minResponse = 0;
    let maxResponse = 0;
    let latestResponse = 0;
    for (let i = this.props.data.length - 1; i >= 0; --i) {
      const response = this.props.data[i].time;
      if (response !== 0) {
        minResponse = minResponse == 0 || response < minResponse ? response : minResponse;
        maxResponse = response > maxResponse ? response : maxResponse;
        if (latestResponse == 0) {
          latestResponse = response;
        }
      }
    }
    avgResponse = (minResponse + maxResponse) / 2;
    return (
      <div style={styles.content}>
        <h4>Response Time</h4>
        Last Response Time: {latestResponse} ms<br />
        Max Response Time: {maxResponse} ms<br />
        Average Response Time: {avgResponse} ms<br />
        <LineChart
          width={500}
          height={300}
          data={this.props.data}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <XAxis dataKey="name" />
          <YAxis />
          <CartesianGrid strokeDasharray="3 3" />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="time" stroke="#8884d8" activeDot={{ r: 8 }} />
        </LineChart>
      </div>
    );
  }
}

export default ResponseTime;
