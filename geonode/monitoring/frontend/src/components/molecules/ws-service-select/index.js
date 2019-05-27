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

  componentWillMount() {
    this.props.getServices();
  }

  componentWillReceiveProps(nextProps) {
    if (this.props.selected) {return;}
    const services = nextProps.services;
    if (services && services.ows_services && services.ows_services.length > 0) {
      this.props.setService(services.ows_services[0].name);
    }
  }

  render() {
    const items = this.props.services
                ? this.props.services.ows_services.map(service => (
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
