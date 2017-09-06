import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import TextField from 'material-ui/TextField';
import Checkbox from 'material-ui/Checkbox';
import RaisedButton from 'material-ui/RaisedButton';
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
    params: PropTypes.object,
  }

  static defaultProps = {
    alertConfig: {
      data: {
        fields: [],
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
      checkbox: {},
      input: {},
    };

    this.handleCheckboxChange = (event, value, id) => {
      const checkboxValue = {};
      checkboxValue[id] = value;
      const newState = {
        ...this.state.checkbox,
        ...checkboxValue,
      };
      this.setState({ checkbox: newState, changed: true });
    };

    this.handleInputChange = (event, id) => {
      const inputValue = {};
      inputValue[id] = event.target.value;
      const newState = {
        ...this.state.checkbox,
        ...inputValue,
      };
      this.setState({ input: newState, changed: true });
    };

    this.handleSubmit = (event) => {
      event.preventDefault();
      if (this.state.changed) {
        console.log('changed');
      }
    };
  }

  componentWillMount() {
    this.props.get(this.props.params.alertId);
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps && nextProps.alertConfig) {
      const fieldStates = { ...this.state };
      nextProps.alertConfig.data.fields.forEach((field) => {
        fieldStates.checkbox[field.id] = field.is_enabled;
      });
      this.setState({ checkbox: fieldStates.checkbox });
    }
  }

  render() {
    const { alertConfig } = this.props;
    return (
      <div style={styles.root}>
        <Header back="/alerts/settings" disableInterval autoRefresh={false} />
        <HoverPaper style={styles.content}>
          <form onSubmit={this.handleSubmit}>
            <div style={styles.heading}>
              <div>
                <div style={styles.title}>
                  <h1>{alertConfig.data.notification.name}</h1>
                  <Checkbox
                    style={styles.title.checkbox}
                    checked={alertConfig.data.notification.active}
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
            />
            <h4 style={styles.when}>When to alert</h4>
            {
            alertConfig.data.fields.map((setting) => (
            <div key={setting.id}>
              <Checkbox
                label={setting.description}
                style={styles.checkbox}
                checked={this.state.checkbox[setting.id]}
                onCheck={(event, value) => this.handleCheckboxChange(event, value, setting.id)}
              />
              <input
                style={styles.number}
                type="number"
                min={setting.min_value ? Number(setting.min_value) : undefined}
                max={setting.max_value ? Number(setting.max_value) : undefined}
                defaultValue={Number(setting.current_value.value)}
                onChange={(event) => this.handleInputChange(event, setting.id)}
              />
              {setting.unit}
            </div>
            ))
            }
          </form>
        </HoverPaper>
      </div>
    );
  }
}


export default AlertConfig;
