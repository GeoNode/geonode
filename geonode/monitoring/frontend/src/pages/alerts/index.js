import React, { Component } from 'react';
import Header from '../../components/organisms/header';
import AlertList from '../../components/organisms/alert-list';
import styles from './styles';


class Alerts extends Component {
  render() {
    return (
      <div style={styles.root}>
        <Header back="/" />
        <AlertList />
      </div>
    );
  }
}


export default Alerts;
