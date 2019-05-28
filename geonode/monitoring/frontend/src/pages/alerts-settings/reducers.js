import ALERT_SETTINGS from './constants';


export default function alertSettings(
  state = { status: 'initial' },
  action,
) {
  switch (action.type) {
    case ALERT_SETTINGS:
      return action.payload;
    default:
      return state;
  }
}
