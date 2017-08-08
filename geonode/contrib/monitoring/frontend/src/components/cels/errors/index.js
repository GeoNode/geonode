import React from 'react';
import PropTypes from 'prop-types';
import HoverPaper from '../../atoms/hover-paper';
import styles from './styles';


class Errors extends React.Component {
  static propTypes = {
    style: PropTypes.object,
  }

  static contextTypes = {
    router: PropTypes.object.isRequired,
  }

  constructor(props) {
    super(props);

    this.handleClick = () => {
      this.context.router.push('/errors');
    };
  }

  render() {
    const style = {
      ...styles.content,
      ...this.props.style,
    };
    return (
      <HoverPaper style={style}>
        <div onClick={this.handleClick} style={styles.clickable}>
          <h3>Errors</h3>
          <span style={styles.stat}>3 Errors occured</span>
        </div>
      </HoverPaper>
    );
  }
}


export default Errors;
