import SERVICES from './constants';


export function services(
  state = { open: false, services: '' },
  action
) {
  switch (action.type) {
    case SERVICES:
      return action.payload;
    default:
      return state;
  }
}
