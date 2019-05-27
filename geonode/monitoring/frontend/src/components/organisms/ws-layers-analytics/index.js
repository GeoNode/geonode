import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { getResponseData, getErrorCount } from '../../../utils';
import HoverPaper from '../../atoms/hover-paper';
import HR from '../../atoms/hr';
import ResponseTable from '../../cels/response-table';
import LayerSelect from '../../cels/layer-select';
import styles from './styles';
import actions from './actions';


const mapStateToProps = (state) => ({
  errorNumber: state.wsLayerError.response,
  interval: state.interval.interval,
  response: state.wsLayerResponse.response,
  timestamp: state.interval.timestamp,
  owsService: state.wsService.service,
});


@connect(mapStateToProps, actions)
class WSLayerAnalytics extends React.Component {
  static propTypes = {
    errorNumber: PropTypes.object,
    getErrors: PropTypes.func.isRequired,
    getResponses: PropTypes.func.isRequired,
    interval: PropTypes.number,
    resetErrors: PropTypes.func.isRequired,
    resetResponses: PropTypes.func.isRequired,
    response: PropTypes.object,
    timestamp: PropTypes.instanceOf(Date),
    owsService: PropTypes.string,
  }

  constructor(props) {
    super(props);
    this.get = (layer, interval = this.props.interval, owsService = this.props.owsService) => {
      this.setState({ layer });
      this.props.getErrors(interval, layer, owsService);
      this.props.getResponses(interval, layer, owsService);
    };

    this.reset = () => {
      this.props.resetErrors();
      this.props.resetResponses();
    };
  }
  componentWillReceiveProps({ timestamp, owsService, interval }) {
    if ((timestamp !== this.props.timestamp || owsService !== this.props.owsService)
        && this.state && this.state.layer) {
      this.get(this.state.layer, interval, owsService);
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
          <h3>W*S Layers Analytics</h3>
          <LayerSelect onChange={this.get} />
        </div>
        <HR />
        <ResponseTable
          average={average}
          max={max}
          requests={requests}
          errorNumber={errorNumber}
        />
      </HoverPaper>
    );
  }
}


export default WSLayerAnalytics;
