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


class AverageCPU extends React.Component {
  static propTypes = {
    cpu: PropTypes.number,
  }

  static contextTypes = {
    muiTheme: PropTypes.object.isRequired,
  }

  render() {
    let cpu = this.props.cpu;
    if (cpu === undefined) {
      cpu = 'N/A';
    } else if (typeof cpu === 'number') {
      if (cpu < 0) {
        cpu = <CircularProgress size={this.context.muiTheme.spinner.size} />;
      } else {
        cpu += '%';
      }
    }
    return (
      <HoverPaper style={styles.content}>
        <h5>Average CPU</h5>
        <div style={styles.stat}>
          <h3>{cpu}</h3>
        </div>
      </HoverPaper>
    );
  }
}


export default AverageCPU;
