import React from 'react';
import PropTypes from 'prop-types';
import TextField from 'material-ui/TextField';
import Checkbox from 'material-ui/Checkbox';
import styles from './styles';


class AlertsSetting extends React.Component {
  static propTypes = {
    autoFocus: PropTypes.bool,
  }

  static defaultProps = {
    autoFocus: false,
  }

  constructor(props) {
    super(props);

    this.handleClick = () => {
    };

    this.handleChange = (/* event */) => {
    };
  }

  render() {
    return (
      <div>
        <TextField
          floatingLabelText="Who to alert:"
          floatingLabelFixed
          hintText="one@example.com, two@example.com, ..."
          fullWidth
          autoFocus={this.props.autoFocus}
          style={styles.who}
        />
        <h4 style={styles.when}>When to alert</h4>
        <div>
          <Checkbox label="GeoNode did not serve any data within 24h" style={styles.checkbox} />
        </div>
        <div>
          <Checkbox label="GeoServer is not responding" style={styles.checkbox} />
        </div>
        <div>
          <Checkbox label="GeoNode is serving more than" style={styles.checkbox} />
          <input
            style={styles.number}
            type="number"
            min={1}
            max={5}
            defaultValue={1}
            onChange={this.handleChange}
          />
          MB/m
        </div>
        <div>
          <Checkbox label="GeoNode error response rate at" style={styles.checkbox} />
          <input
            style={styles.number}
            type="number"
            min={1}
            max={5}
            defaultValue={1}
          />
          err/m
        </div>
        <div>
          <Checkbox label="GeoServer's error is at least rate at" style={styles.checkbox} />
          <input
            style={styles.number}
            type="number"
            min={1}
            max={5}
            defaultValue={1}
          />
          err/m
        </div>
      </div>
    );
  }
}


export default AlertsSetting;
