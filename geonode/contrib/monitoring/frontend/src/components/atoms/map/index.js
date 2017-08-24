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

    this.renderMap = (
      { data, fills } = this.parse(this.props.countryData),
    ) => {
      while (this.d3Element.hasChildNodes()) {
        this.d3Element.removeChild(this.d3Element.lastChild);
      }
      const basicChoropleth = new Datamap({
        data,
        fills,
        element: this.d3Element,
        width: '100%',
        height: '200',
        setProjection: (element) => {
          const x = element.offsetWidth / 2;
          const y = element.offsetHeight / 2 + 40;
          const projection = d3.geoMercator().scale(50).translate([x, y]);
          const path = d3.geoPath().projection(projection);
          return { path, projection };
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

    this.parseCountries = (data) => {
      if (!data || !data.data) {
        return undefined;
      }
      const realData = data.data.data[0];
      if (realData.data.length === 0) {
        return undefined;
      }
      const result = {};
      realData.data.forEach((country) => {
        result[country.label] = { val: country.val };
      });
      return result;
    };

    this.calculateFills = (data) => {
      const defaultFill = '#ccc';
      const fills = {
        defaultFill,
        'no data': defaultFill,
      };
      if (!data) {
        return { data, fills };
      }
      const realCountries = {};
      Object.keys(data).forEach((countryName) => {
        if (countryName.length === 3) {
          realCountries[countryName] = data[countryName];
        }
      });
      const max = Object.keys(realCountries).reduce((currentMax, countryName) => {
        const val = Number(realCountries[countryName].val);
        return val > currentMax ? val : currentMax;
      }, 0);
      const step = Math.floor(max / 5);
      let color = 7;
      for (let multiplier = 0; multiplier < 5; ++multiplier) {
        const low = multiplier * step;
        const hi = (multiplier + 1) * step;
        fills[`${low}-${hi}`] = `#${color}${color}c`;
        --color;
      }
      const countryData = {};
      Object.keys(realCountries).forEach((countryName) => {
        const val = Number(realCountries[countryName].val);
        const newCountry = JSON.parse(JSON.stringify(realCountries[countryName]));
        for (let multiplier = 1; multiplier <= 5; ++multiplier) {
          if (multiplier * step >= val) {
            const low = (multiplier - 1) * step;
            const hi = multiplier * step;
            newCountry.fillKey = `${low}-${hi}`;
            break;
          }
        }
        countryData[countryName] = newCountry;
      });
      return { data: countryData, fills };
    };

    this.parse = (rawData) => {
      const { data, fills } = this.calculateFills(
        this.parseCountries(rawData),
      );
      return { data, fills };
    };
  }

  componentWillMount() {
    this.get();
  }

  componentDidMount() {
    this.renderMap();
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps) {
      if (nextProps.timestamp && nextProps.timestamp !== this.props.timestamp) {
        this.get(nextProps.interval);
      }
    }
  }

  componentDidUpdate() {
    this.renderMap();
  }

  componentWillUnmount() {
    this.props.reset();
  }

  render() {
    return (
      <div style={styles.root} ref={(node) => {this.d3Element = node;}} />
    );
  }
}


export default WorldMap;
