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
import DropDownMenu from 'material-ui/DropDownMenu';
import MenuItem from 'material-ui/MenuItem';
import actions from './actions';
import styles from './styles';


const mapStateToProps = (state) => ({
  interval: state.interval.interval,
  layers: state.layerList.response,
  timestamp: state.interval.timestamp,
});


@connect(mapStateToProps, actions)
class GeonodeData extends React.Component {
  static defaultProps = {
    fetch: true,
  }

  static propTypes = {
    fetch: PropTypes.bool,
    get: PropTypes.func.isRequired,
    interval: PropTypes.number,
    layers: PropTypes.array,
    reset: PropTypes.func.isRequired,
    onChange: PropTypes.func,
    response: PropTypes.object,
    timestamp: PropTypes.instanceOf(Date),
  }

  constructor(props) {
    super(props);

    this.state = {};

    this.handleChange = (target, id, name) => {
      if (this.props.onChange && this.props.layers[id]) {
        this.setState({ selected: name });
        this.props.onChange(this.props.layers[id].id);
      }
    };
  }

  componentWillMount() {
    if (this.props.fetch) {
      this.props.get();
    }
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps && nextProps.layers && nextProps.layers.length > 0) {
      const layer = nextProps.layers[0];
      const selected = layer.name;
      this.setState({ selected });
      if (this.props.onChange) {
        this.props.onChange(layer.id);
      }
    }
  }

  render() {
    const layers = this.props.layers
                 ? this.props.layers.map((layer) => (
                   <MenuItem
                     key={layer.id}
                     value={layer.name}
                     primaryText={layer.name}
                   />
                 )) : null;
    return (
      <DropDownMenu
        style={styles.root}
        value={this.state.selected}
        onChange={this.handleChange}
      >
        {layers}
      </DropDownMenu>
    );
  }
}


export default GeonodeData;
