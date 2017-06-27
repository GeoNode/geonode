import React from 'react';
import PropTypes from 'prop-types';
import HoverPaper from '../../atoms/hover-paper';
import styles from './styles';


class Errors extends React.Component {
  static propTypes = {
    style: PropTypes.object,
  }

  render() {
    const style = {
      ...styles.content,
      ...this.props.style,
    };
    return (
      <HoverPaper style={style}>
        <h3>Errors</h3>
        <span style={styles.stat}>3 Errors occured</span>
      </HoverPaper>
    );
  }
}


export default Errors;
