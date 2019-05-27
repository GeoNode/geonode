import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import styles from './styles';
import actions from './actions';


const mapStateToProps = (state) => ({
  interval: state.interval.interval,
  layers: state.frequentLayers.response,
  timestamp: state.interval.timestamp,
});


@connect(mapStateToProps, actions)
class Alert extends React.Component {
  static propTypes = {
    get: PropTypes.func.isRequired,
    interval: PropTypes.number,
    layers: PropTypes.object,
    timestamp: PropTypes.instanceOf(Date),
  };

  static defaultProps = {
    layers: {
      data: {
        data: [{
          data: [],
        }],
      },
    },
  }

  constructor(props) {
    super(props);

    this.get = (interval = this.props.interval) => {
      this.props.get(interval);
    };
  }

  componentWillMount() {
    this.get();
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps) {
      if (nextProps.timestamp && nextProps.timestamp !== this.props.timestamp) {
        this.get(nextProps.interval);
      }
    }
  }

  render() {
    const layersData = this.props.layers.data.data[0].data;
    const layers = layersData.map((layer, index) => (
        <tr key={layer.resource.name}>
          <th scope="row">{index + 1}</th>
          <td>{layer.resource.name}</td>
          <td>{Number(layer.val)}</td>
        </tr>
    ));
    return (
      <div style={styles.root}>
        <h5 style={styles.title}>Most Frequently Accessed Layers</h5>
        <table style={styles.table}>
          <tbody>
            <tr>
              <th scope="row"></th>
              <td>Layer Name</td>
              <td>Requests</td>
            </tr>
            {layers}
          </tbody>
        </table>
      </div>
    );
  }
}


export default Alert;
