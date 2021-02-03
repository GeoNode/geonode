/*
#########################################################################
#
# Copyright (C) 2019 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################
*/

import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import TextField from 'material-ui/TextField';
import Checkbox from 'material-ui/Checkbox';
import RaisedButton from 'material-ui/RaisedButton';
import DropDownMenu from 'material-ui/DropDownMenu';
import MenuItem from 'material-ui/MenuItem';
import { stateToData, stateToFields } from '../../utils';
import HoverPaper from '../../components/atoms/hover-paper';
import Header from '../../components/organisms/header';
import actions from './actions';
import styles from './styles';


const mapStateToProps = (state) => ({
  alertConfig: state.alertConfig.response,
});


@connect(mapStateToProps, actions)
class AlertConfig extends React.Component {
  static propTypes = {
    alertConfig: PropTypes.object,
    get: PropTypes.func.isRequired,
    match: PropTypes.object,
    set: PropTypes.func.isRequired,
  }

  static defaultProps = {
    alertConfig: {
      data: {
        fields: [],
        emails: [],
        notification: {
          active: false,
          description: '',
          name: '',
        },
      },
    },
  }

  constructor(props) {
    super(props);

    this.state = {
      emails: '',
    };

    this.handleSubmit = (event) => {
      event.preventDefault();
      const data = stateToData(this.state);
      this.props.set(this.props.match.params.alertId, data);
    };

    this.handleInputChange = (event, name) => {
      const result = {};
      result[name] = { ...this.state[name] };
      if (!result[name].current_value) {
        result[name].current_value = {};
      }
      result[name].current_value.value = event.target.value;
      this.setState({ ...result });
    };

    this.handleCheckboxChange = (event, value, name) => {
      const result = {};
      result[name] = { ...this.state[name] };
      result[name].is_enabled = value;
      this.setState({ ...result });
    };

    this.handleActiveChange = (event, active) => {
      this.setState({ active });
    };

    this.handleEmailsChange = (event, value) => {
      this.setState({ emails: value });
    };

    this.handleDropdownChange = (event, key, value, name) => {
      const result = {};
      result[name] = this.state[name];
      result[name].current_value.value = Number(value);
      this.setState({ ...result });
    };
  }

  componentWillMount() {
    this.props.get(this.props.match.params.alertId);
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps && nextProps.alertConfig) {
      nextProps.alertConfig.data.fields.forEach((field) => {
        const data = {};
        data[field.field_name] = field;
        const min = field.min_value
                  ? Number(field.min_value)
                  : undefined;
        const max = field.max_value
                  ? Number(field.max_value)
                  : undefined;
        let defaultValue;
        if (!data[field.field_name].current_value) {
          data[field.field_name].current_value = {};
        }
        if (data[field.field_name].current_value.value) {
          defaultValue = Number(data[field.field_name].current_value.value);
        } else if (min) {
          defaultValue = min;
        } else if (max) {
          defaultValue = max;
        }
        data[field.field_name].current_value.value = defaultValue;
        this.setState(data);
      });
      this.setState({ active: nextProps.alertConfig.data.notification.active });
      this.setState({ emails: nextProps.alertConfig.data.emails.join(', ') });
    }
  }

  render() {
    const { alertConfig } = this.props;
    const data = stateToFields(this.state).map((settingName) => {
      const setting = this.state[settingName];
      const min = setting.min_value
                ? Number(setting.min_value)
                : undefined;
      const max = setting.max_value
                ? Number(setting.max_value)
                : undefined;
      let input;
      if (setting.steps) {
        const items = setting.steps_calculated.map(
          (step) => (
            <MenuItem
              key={Number(step)}
              value={Number(step)}
              primaryText={Number(step)}
            />
          )
        );
        input = (
          <DropDownMenu
            value={setting.current_value.value}
            onChange={
              (event, key, value) =>
                this.handleDropdownChange(event, key, value, settingName)
            }
          >
            {items}
          </DropDownMenu>
        );
      } else {
        input = (
          <input
            style={styles.number}
            type="number"
            min={min}
            max={max}
            defaultValue={setting.current_value.value}
            onChange={(event) => this.handleInputChange(event, settingName)}
          />
        );
      }
      return (
        <div key={settingName} style={styles.checks}>
          <Checkbox
            label={setting.description}
            style={styles.checkbox}
            checked={setting.is_enabled}
            onCheck={(event, value) => this.handleCheckboxChange(event, value, settingName)}
          />
          {input}
          {setting.unit}
        </div>
      );
    });
    return (
      <div style={styles.root}>
        <Header back="/alerts-settings" disableInterval autoRefresh={false} />
        <HoverPaper style={styles.content}>
          <form onSubmit={this.handleSubmit}>
            <div style={styles.heading}>
              <div>
                <div style={styles.title}>
                  <h1>{alertConfig.data.notification.name}</h1>
                  <Checkbox
                    style={styles.title.checkbox}
                    checked={this.state.active}
                    onCheck={this.handleActiveChange}
                  />
                </div>
                <h4>{alertConfig.data.notification.description}</h4>
              </div>
              <RaisedButton label="save" type="submit" />
            </div>
            <TextField
              floatingLabelText="Who to alert:"
              floatingLabelFixed
              hintText="one@example.com, two@example.com, ..."
              fullWidth
              autoFocus
              style={styles.who}
              value={this.state.emails}
              onChange={this.handleEmailsChange}
            />
            <h4 style={styles.when}>When to alert</h4>
            {data}
          </form>
        </HoverPaper>
      </div>
    );
  }
}


export default AlertConfig;
