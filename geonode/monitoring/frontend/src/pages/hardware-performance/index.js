import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import Header from '../../components/organisms/header';
import GeonodeStatus from '../../components/organisms/geonode-status';
import GeoserverStatus from '../../components/organisms/geoserver-status';
import styles from './styles';


const mapStateToProps = (state) => ({
  services: state.services.hostgeoserver,
});


@connect(mapStateToProps)
class HWPerf extends React.Component {
  static propTypes = {
    services: PropTypes.array,
  }

  render() {
    return (
      <div style={styles.root}>
        <Header back="/" />
        <div style={styles.analytics}>
          <GeonodeStatus />
          {
            this.props.services
            ? <GeoserverStatus />
            : false
          }
        </div>
      </div>
    );
  }
}


export default HWPerf;
