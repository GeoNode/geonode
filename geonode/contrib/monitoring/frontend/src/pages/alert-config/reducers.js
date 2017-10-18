import { ALERT_CONFIG_GET, ALERT_CONFIG_SET } from './constants';


export function alertConfig(
  state = { status: 'initial' },
  action,
) {
  switch (action.type) {
    case ALERT_CONFIG_GET:
      return action.payload;
    default:
      return state;
  }
}


export function alertConfigSave(
  state = { status: 'initial' },
  action,
) {
  switch (action.type) {
    case ALERT_CONFIG_SET:
      return action.payload;
    default:
      return state;
  }
}
