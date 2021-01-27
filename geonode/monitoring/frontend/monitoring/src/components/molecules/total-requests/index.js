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
import CircularProgress from 'material-ui/CircularProgress';
import HoverPaper from '../../atoms/hover-paper';
import styles from './styles';


class TotalRequests extends React.Component {
  static propTypes = {
    requests: PropTypes.number,
  }

  static contextTypes = {
    muiTheme: PropTypes.object.isRequired,
  }

  render() {
    let requests = this.props.requests;
    if (requests === undefined) {
      requests = 'N/A';
    } else if (typeof requests === 'number') {
      if (requests < 0) {
        requests = <CircularProgress size={this.context.muiTheme.spinner.size} />;
      }
    }
    return (
      <HoverPaper style={styles.content}>
        <h5>Total Requests</h5>
        <div style={styles.stat}>
          <h3>{requests}</h3>
        </div>
      </HoverPaper>
    );
  }
}


export default TotalRequests;
