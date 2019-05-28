import UPTIME from './constants';

export default function uptime(
  state = { status: 'initial' },
  action,
) {
  switch (action.type) {
    case UPTIME:
      return action.payload;
    default:
      return state;
  }
}
