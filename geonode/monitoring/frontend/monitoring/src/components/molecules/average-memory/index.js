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


class AverageMemory extends React.Component {
  static propTypes = {
    mem: PropTypes.number,
  }

  static contextTypes = {
    muiTheme: PropTypes.object.isRequired,
  }

  render() {
    let mem = this.props.mem;
    if (mem === undefined) {
      mem = 'N/A';
    } else if (typeof mem === 'number') {
      if (mem < 0) {
        mem = <CircularProgress size={this.context.muiTheme.spinner.size} />;
      } else {
        const mbMem = (mem / 1024 / 1024);
        let mbMemFormated;
        if (mbMem < 10) {
          mbMemFormated = mbMem.toFixed(2);
        } else if (mbMem < 100) {
          mbMemFormated = mbMem.toFixed(1);
        } else {
          mbMemFormated = Math.floor(mbMem);
        }
        mem = `${mbMemFormated} MB`;
      }
    }
    return (
      <HoverPaper style={styles.content}>
        <h5>Average Memory</h5>
        <div style={styles.stat}>
          <h3>{mem}</h3>
        </div>
      </HoverPaper>
    );
  }
}


export default AverageMemory;
