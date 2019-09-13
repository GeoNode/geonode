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
import { Link } from 'react-router-dom';
import HR from '../../atoms/hr';


class AlertsSetting extends React.Component {
  static propTypes = {
    alert: PropTypes.object.isRequired,
    autoFocus: PropTypes.bool,
  }

  static defaultProps = {
    autoFocus: false,
  }

  render() {
    return (
      <div>
        <HR />
        <Link to={`/alerts/${this.props.alert.id}`}>
          <h4>{this.props.alert.name}</h4>
        </Link>
        {this.props.alert.description}
      </div>
    );
  }
}


export default AlertsSetting;
