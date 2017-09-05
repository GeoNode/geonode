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

  componentWillMount() {
    this.props.get(this.props.params.alertId);
  }

  render() {
    const { alertConfig } = this.props;
    return (
      <div style={styles.root}>
        <Header back="/alerts/settings" disableInterval autoRefresh={false} />
        <HoverPaper style={styles.content}>
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
            <RaisedButton label="save" />
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
                  checked={setting.is_enabled}
                />
                <input
                  style={styles.number}
                  type="number"
                  min={setting.min_value ? Number(setting.min_value) : undefined}
                  max={setting.max_value ? Number(setting.max_value) : undefined}
                  defaultValue={Number(setting.current_value.value)}
                  onChange={this.handleChange}
                />
                MB/m
              </div>
            ))
          }
        </HoverPaper>
      </div>
    );
  }
}


export default AlertConfig;
