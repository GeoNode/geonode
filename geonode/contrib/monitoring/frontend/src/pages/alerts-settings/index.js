import React, { Component } from 'react';
import RaisedButton from 'material-ui/RaisedButton';
import TextField from 'material-ui/TextField';
import Checkbox from 'material-ui/Checkbox';
import Header from '../../components/organisms/header';
import HoverPaper from '../../components/atoms/hover-paper';
import styles from './styles';


class AlertsSettings extends Component {
  constructor(props) {
    super(props);

    this.handleClick = () => {
      console.log('organisms/alert-list save button');
    };

    this.handleChange = (event) => {
      console.log(event.target.value);
    };
  }

  render() {
    return (
      <div style={styles.root}>
        <Header back="/alerts" disableInterval autoRefresh={false} />
        <HoverPaper style={styles.content}>
          <div style={styles.header}>
            <h3>Alerts Settings</h3>
            <RaisedButton
              onClick={this.handleClick}
              style={styles.icon}
              label="save"
            />
          </div>
          <TextField
            floatingLabelText="Who to alert:"
            floatingLabelFixed
            hintText="one@example.com, two@example.com, ..."
            fullWidth
            autoFocus
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
        </HoverPaper>
      </div>
    );
  }
}


export default AlertsSettings;
