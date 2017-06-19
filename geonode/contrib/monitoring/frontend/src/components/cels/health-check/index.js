import React, { Component } from 'react';
import HoverPaper from '../../atoms/hover-paper';
import X from 'material-ui/svg-icons/content/clear';
import styles from './styles';


class HealthCheck extends Component {
  render() {
    const style = {
      ...styles.content,
      ...this.props.style,
    };
    return (
      <HoverPaper style={style}>
        <h3>Health Check</h3>
        <X style={styles.icon} />
      </HoverPaper>
    );
  }
}


HealthCheck.propTypes = {
  style: React.PropTypes.object,
};


export default HealthCheck;
