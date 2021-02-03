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
import HoverPaper from '../../atoms/hover-paper';
import styles from './styles';


class Alert extends React.Component {
  static propTypes = {
    alert: PropTypes.object.isRequired,
  }

  constructor(props) {
    super(props);

    this.state = {
      detail: false,
    };

    this.handleClick = () => {
      this.setState({ detail: !this.state.detail });
    };
  }

  render() {
    const { alert } = this.props;
    const visibilityStyle = this.state.detail
                          ? styles.shownDetail
                          : styles.hiddenDetail;
    const style = alert.severity === 'error'
                ? { ...styles.short, color: '#d12b2b' }
                : styles.short;
    return (
      <HoverPaper style={styles.content} onClick={this.handleClick}>
        <div style={style}>
          {alert.message}
        </div>
        {alert.spotted_at.replace(/T/, ' ')}
        <div style={visibilityStyle}>
          {alert.description}
        </div>
      </HoverPaper>
    );
  }
}


export default Alert;
