import ALERT_LIST from './constants';


export default function alertList(
  state = { status: 'initial' },
  action,
) {
  switch (action.type) {
    case ALERT_LIST:
      return action.payload;
    default:
      return state;
  }
}
