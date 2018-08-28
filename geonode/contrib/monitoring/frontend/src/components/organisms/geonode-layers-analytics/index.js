import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { getResponseData, getErrorCount } from '../../../utils';
import HoverPaper from '../../atoms/hover-paper';
import HR from '../../atoms/hr';
import ResponseTable from '../../cels/response-table';
import LayerSelect from '../../cels/layer-select';
import FrequentLayers from '../../cels/frequent-layers';
import styles from './styles';
import actions from './actions';


const mapStateToProps = (state) => ({
  interval: state.interval.interval,
  response: state.geonodeLayerResponse.response,
  errorNumber: state.geonodeLayerError.response,
});


@connect(mapStateToProps, actions)
class GeonodeLayerAnalytics extends React.Component {
  static propTypes = {
    getResponses: PropTypes.func.isRequired,
    resetResponses: PropTypes.func.isRequired,
    getErrors: PropTypes.func.isRequired,
    resetErrors: PropTypes.func.isRequired,
    interval: PropTypes.number,
    response: PropTypes.object,
    errorNumber: PropTypes.object,
    timestamp: PropTypes.instanceOf(Date),
  }

  constructor(props) {
    super(props);
    this.get = (layer, interval = this.props.interval) => {
      this.setState({ layer });
      this.props.getErrors(layer, interval);
      this.props.getResponses(layer, interval);
    };

    this.reset = () => {
      this.props.resetErrors();
      this.props.resetResponses();
    };
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps) {
      if (
        nextProps.timestamp && nextProps.timestamp !== this.props.timestamp
        && this.state && this.state.layer
      ) {
        this.get(this.state.layer, nextProps.interval);
      }
    }
  }

  componentWillUnmount() {
    this.reset();
  }

  render() {
    let average = 0;
    let max = 0;
    let requests = 0;
    [
      average,
      max,
      requests,
    ] = getResponseData(this.props.response);
    const errorNumber = getErrorCount(this.props.errorNumber);
    return (
      <HoverPaper style={styles.content}>
        <div style={styles.header}>
          <h3>Geonode Layers Analytics</h3>
          <LayerSelect onChange={this.get} />
        </div>
        <HR />
        <ResponseTable
          average={average}
          max={max}
          requests={requests}
          errorNumber={errorNumber}
        />
        <FrequentLayers />
      </HoverPaper>
    );
  }
}


export default GeonodeLayerAnalytics;
