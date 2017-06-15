import React, { Component } from 'react';
import HoverPaper from '../../atoms/hover-paper';
import styles from './styles';


class Map extends Component {
  render() {
    return (
      <HoverPaper style={styles.content} />
    );
  }
}


export default Map;
