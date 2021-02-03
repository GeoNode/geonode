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


const mapStateToProps = (state) => ({
  services: state.wsServices.response,
  selected: state.wsService.service,
});


@connect(mapStateToProps, actions)
class WSServiceSelect extends React.Component {
  static propTypes = {
    selected: PropTypes.string,
    services: PropTypes.object,
    getServices: PropTypes.func.isRequired,
    setService: PropTypes.func.isRequired,
  }

  constructor(props) {
    super(props);

    this.handleServiceSelect = (event, index, value) => {
      this.props.setService(value);
    };
  }

  UNSAFE_componentWillMount() {
    this.props.getServices();
  }
  
  UNSAFE_componentWillReceiveProps(nextProps) {
    if (this.props.selected) {return;}
    const services = nextProps.services;
    if (services && services.event_types && services.event_types.length > 0) {
      const firstSelected = services.event_types.find(({ name }) => name === 'OWS:ALL') || services.event_types[0];
      this.props.setService(firstSelected && firstSelected.name);
    }
  }

  render() {
    const items = this.props.services
                ? this.props.services.event_types.map(service => (
                  <MenuItem
                    key={service.name}
                    value={service.name}
                    primaryText={service.name}
                  />
                ))
                : [];
    return (
      <DropDownMenu
        value={this.props.selected}
        onChange={this.handleServiceSelect}
      >
        {items}
      </DropDownMenu>
    );
  }
}


export default WSServiceSelect;
