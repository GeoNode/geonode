import { createAction } from 'redux-actions';
import { BACKEND, NOTIFICATIONS } from './constants';


const open = createAction(NOTIFICATIONS, notifications => ({
  notifications,
  open: true,
}));


const close = createAction(NOTIFICATIONS, () => ({
  notifications: '',
  open: false,
}));


const setBackendUrl = createAction(BACKEND, hostname => ({
  apiUrl: `http://${hostname}:5000/api/v0`,
}));


const actions = {
  open,
  close,
  setBackendUrl,
};

export default actions;
