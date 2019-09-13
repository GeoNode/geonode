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
import Paper from 'material-ui/Paper';


class HoverPaper extends React.Component {
  static propTypes = {
    children: PropTypes.node,
    style: PropTypes.object,
    onClick: PropTypes.func,
  }

  constructor(props) {
    super(props);

    this.state = {
      zDepth: 1,
    };

    this.handleMouseOver = () => {
      this.setState({ zDepth: 3 });
    };

    this.handleMouseOut = () => {
      this.setState({ zDepth: 1 });
    };
  }

  render() {
    return (
      <Paper
        style={this.props.style}
        onMouseOver={this.handleMouseOver}
        onMouseOut={this.handleMouseOut}
        zDepth={this.state.zDepth}
        onClick={this.props.onClick}
      >
        {this.props.children}
      </Paper>
    );
  }
}


export default HoverPaper;
