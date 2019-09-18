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
import HR from '../../atoms/hr';
import styles from './styles';


class ResponseTable extends React.Component {
  static propTypes = {
    average: PropTypes.number,
    errorNumber: PropTypes.number,
    max: PropTypes.number,
    requests: PropTypes.number,
  }

  render() {
    const average = this.props.average != undefined ? `${this.props.average} ms` : 'N/A';
    const max = this.props.max != undefined ? `${this.props.max} ms` : 'N/A';
    const requests = this.props.requests != undefined ? this.props.requests : 0;
    return (
      <div style={styles.content}>
        <h4>Average Response Time {average}</h4>
        <HR />
        <h4>Max Response Time {max}</h4>
        <HR />
        <h4>Total Requests {requests}</h4>
        <HR />
        <h4>Total Errors {this.props.errorNumber}</h4>
      </div>
    );
  }
}


export default ResponseTable;
