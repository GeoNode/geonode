import React from 'react';
import PropTypes from 'prop-types';
import HoverPaper from '../../atoms/hover-paper';
import styles from './styles';


class AlertList extends React.Component {
  static propTypes = {
    short: PropTypes.string.isRequired,
    offending: PropTypes.string.isRequired,
    threshold: PropTypes.string.isRequired,
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
    const detail = this.state.detail
                 ? <div style={styles.shownDetail}>
                     offending value: {this.props.offending}<br />
                     threshold: {this.props.threshold}
                   </div>
                 : <div style={styles.hiddenDetail}>
                     offending value: {this.props.offending}<br />
                     threshold: {this.props.threshold}
                   </div>;
    return (
      <HoverPaper style={styles.content} onClick={this.handleClick}>
        <div style={styles.short}>
          {this.props.short}
        </div>
        {detail}
      </HoverPaper>
    );
  }
}


export default AlertList;
