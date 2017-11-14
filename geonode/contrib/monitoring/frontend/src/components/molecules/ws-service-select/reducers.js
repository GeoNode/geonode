import { WS_SERVICES, WS_SERVICE } from './constants';


export function wsServices(
  state = { status: 'initial' },
  action,
) {
  switch (action.type) {
    case WS_SERVICES:
      return action.payload;
    default:
      return state;
  }
}


export function wsService(
  state = { status: 'initial' },
  action,
) {
  switch (action.type) {
    case WS_SERVICE:
      return action.payload;
    default:
      return state;
  }
}
