import React from 'react';
import PropTypes from 'prop-types';
import Header from '../../components/organisms/header';
import styles from './styles';


class AlertDetails extends React.Component {
  static propTypes = {
    params: PropTypes.object,
  }

  render() {
    return (
      <div style={styles.root}>
        <Header back="/alerts" disableInterval autoRefresh={false} />
        <h1>Alert Details for id {this.props.params.alertId}</h1>
      </div>
    );
  }
}


export default AlertDetails;
