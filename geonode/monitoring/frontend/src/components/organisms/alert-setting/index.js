import React from 'react';
import PropTypes from 'prop-types';
import { Link } from 'react-router';
import HR from '../../atoms/hr';


class AlertsSetting extends React.Component {
  static propTypes = {
    alert: PropTypes.object.isRequired,
    autoFocus: PropTypes.bool,
  }

  static defaultProps = {
    autoFocus: false,
  }

  render() {
    return (
      <div>
        <HR />
        <Link to={`/alerts/${this.props.alert.id}`}>
          <h4>{this.props.alert.name}</h4>
        </Link>
        {this.props.alert.description}
      </div>
    );
  }
}


export default AlertsSetting;
