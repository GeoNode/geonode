import React from 'react';
import PropTypes from 'prop-types';
import HoverPaper from '../../atoms/hover-paper';
import styles from './styles';


class Alert extends React.Component {
  static propTypes = {
    alert: PropTypes.object.isRequired,
  }

  constructor(props) {
    super(props);

    this.state = {
      detail: false,
    };

    this.handleClick = () => {
      this.setState({ detail: !this.state.detail });
    };
  }

  render() {
    const { alert } = this.props;
    const visibilityStyle = this.state.detail
                          ? styles.shownDetail
                          : styles.hiddenDetail;
    const style = alert.severity === 'error'
                ? { ...styles.short, color: '#d12b2b' }
                : styles.short;
    return (
      <HoverPaper style={styles.content} onClick={this.handleClick}>
        <div style={style}>
          {alert.message}
        </div>
        {alert.spotted_at.replace(/T/, ' ')}
        <div style={visibilityStyle}>
          {alert.description}
        </div>
      </HoverPaper>
    );
  }
}


export default Alert;
