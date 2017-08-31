import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import DropDownMenu from 'material-ui/DropDownMenu';
import MenuItem from 'material-ui/MenuItem';
import actions from './actions';


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
    response: PropTypes.object,
    timestamp: PropTypes.instanceOf(Date),
  }

  constructor(props) {
    super(props);

    this.state = {};
  }

  componentWillMount() {
    if (this.props.fetch) {
      this.props.get();
    }
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps && nextProps.layers && nextProps.layers.length > 0) {
      const selected = nextProps.layers[0].name;
      this.setState({ selected });
    }
  }

  componentWillUnmount() {
    this.props.reset();
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
      <DropDownMenu value={this.state.selected}>
        {layers}
      </DropDownMenu>
    );
  }
}


export default GeonodeData;
