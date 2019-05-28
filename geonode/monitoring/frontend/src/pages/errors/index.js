import React, { Component } from 'react';
import Header from '../../components/organisms/header';
import ErrorList from '../../components/organisms/error-list';
import styles from './styles';


class Errors extends Component {
  render() {
    return (
      <div style={styles.root}>
        <Header back="/" />
        <ErrorList />
      </div>
    );
  }
}


export default Errors;
