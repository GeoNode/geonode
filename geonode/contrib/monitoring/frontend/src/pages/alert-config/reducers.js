import ALERT_CONFIG from './constants';


export default function alertConfig(
  state = { status: 'initial' },
  action,
) {
  switch (action.type) {
    case ALERT_CONFIG:
      return action.payload;
    default:
      return state;
  }
}
