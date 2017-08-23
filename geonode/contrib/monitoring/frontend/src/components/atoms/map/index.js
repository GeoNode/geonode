import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import Datamap from 'datamaps';
import * as d3 from 'd3';
import styles from './styles';
import actions from './actions';


const mapStateToProps = (state) => ({
  countryData: state.mapData.response,
  interval: state.interval.interval,
  timestamp: state.interval.timestamp,
});


@connect(mapStateToProps, actions)
class WorldMap extends React.Component {
  static propTypes = {
    countryData: PropTypes.object,
    get: PropTypes.func.isRequired,
    interval: PropTypes.number,
    reset: PropTypes.func.isRequired,
    timestamp: PropTypes.instanceOf(Date),
  }

  constructor(props) {
    super(props);

    this.renderMap = (data) => {
      const basicChoropleth = new Datamap({
        data,
        element: this.d3Element,
        width: '100%',
        height: '200',
        setProjection: (element) => {
          const x = element.offsetWidth / 2;
          const y = element.offsetHeight / 2 + 40;
          const projection = d3.geoMercator()
            .scale(50)
            .translate([x, y]);
          const path = d3.geoPath()
            .projection(projection);
          return { path, projection };
        },
        fills: {
          defaultFill: '#cccccc',
          '0-1': '#9999cc',
          '1-2': '#8888cc',
          '2-3': '#7777cc',
          '3-4': '#6666cc',
          '4-5': '#5555cc',
          '5-6': '#4444cc',
          '6-7': '#3333cc',
          '7-8': '#2222cc',
          '8-9': '#1111cc',
          '9-10': '#0000cc',
        },
        geographyConfig: {
          popupTemplate: (geography, popupData) => {
            let popup = '<div class="hoverinfo"><strong>';
            popup += `${geography.properties.name}: ${popupData.val}`;
            popup += '</strong></div>';
            return popup;
          },
        },
      });
      basicChoropleth.legend();
    };

    this.get = (interval = this.props.interval) => {
      this.props.get(interval);
    };

    this.parseData = (data) => {
      const result = {};
      if (!data || !data.data) {
        return result;
      }
      const realData = data.data.data[0];
      if (realData.data.length === 0) {
        return result;
      }
      realData.data.forEach((country) => {
        result[country.label] = {
          fillKey: '9-10',
          val: country.val,
        };
      });
      return result;
    };
  }

  componentWillMount() {
    this.get();
  }

  componentDidMount() {
    this.renderMap(this.parseData(this.props.countryData));
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps) {
      if (nextProps.timestamp && nextProps.timestamp !== this.props.timestamp) {
        this.get(nextProps.interval);
      }
    }
  }

  componentDidUpdate() {
    while (this.d3Element.hasChildNodes()) {
      this.d3Element.removeChild(this.d3Element.lastChild);
    }
    this.renderMap(this.parseData(this.props.countryData));
  }

  componentWillUnmount() {
    this.props.reset();
  }

  render() {
    this.parseData(this.props.countryData);
    return (
      <div style={styles.root} ref={(node) => {this.d3Element = node;}} />
    );
  }
}


export default WorldMap;
