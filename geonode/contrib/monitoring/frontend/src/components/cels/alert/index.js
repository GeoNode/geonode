import React from 'react';
import PropTypes from 'prop-types';
import HoverPaper from '../../atoms/hover-paper';
import styles from './styles';


class AlertList extends React.Component {
  static propTypes = {
    date: PropTypes.string.isRequired,
    short: PropTypes.string.isRequired,
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
                     more detailed text
                   </div>
                 : <div style={styles.hiddenDetail}>
                     more detailed text
                   </div>
                 ;
    return (
      <HoverPaper style={styles.content} onClick={this.handleClick}>
        <div style={styles.date}>
          {this.props.date}
        </div>
        <div style={styles.short}>
          {this.props.short}
        </div>
        {detail}
      </HoverPaper>
    );
  }
}


export default AlertList;
