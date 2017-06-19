import { BACKEND, NOTIFICATIONS } from './constants';


export function notifications(
  state = { open: false, notifications: '' },
  action
) {
  switch (action.type) {
    case NOTIFICATIONS:
      return action.payload;
    default:
      return state;
  }
}


export function backend(state = { status: 'initial' }, action) {
  switch (action.type) {
    case BACKEND: {
      return action.payload;
    }
    default:
      return state;
  }
}
