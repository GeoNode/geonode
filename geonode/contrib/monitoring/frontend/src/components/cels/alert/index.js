import React from 'react';
import PropTypes from 'prop-types';
import { Link } from 'react-router';
import HoverPaper from '../../atoms/hover-paper';
import styles from './styles';


class AlertList extends React.Component {
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
    const alert = this.props.alert;
    const alertContent = (
      <div>
        offending value: {alert.offending_value}<br />
        threshold: {alert.threshold_value}<br />
        config: <Link to={`/alerts/${alert.check_id}`}>link</Link>
      </div>
    );
    const detail = this.state.detail
                 ? <div style={styles.shownDetail}>
                     {alertContent}
                   </div>
                 : <div style={styles.hiddenDetail}>
                     {alertContent}
                 </div>
    ;
    return (
      <HoverPaper style={styles.content} onClick={this.handleClick}>
        <div style={styles.short}>
          {alert.message}
        </div>
        {detail}
      </HoverPaper>
    );
  }
}


export default AlertList;
