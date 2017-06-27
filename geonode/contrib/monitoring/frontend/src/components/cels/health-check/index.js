import React from 'react';
import PropTypes from 'prop-types';
import HoverPaper from '../../atoms/hover-paper';
import X from 'material-ui/svg-icons/content/clear';
import styles from './styles';


class HealthCheck extends React.Component {
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
        <h3>Health Check</h3>
        <X style={styles.icon} />
      </HoverPaper>
    );
  }
}


export default HealthCheck;
