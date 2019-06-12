import { createAction } from 'redux-actions';
import { fetch } from '../../utils';
import apiUrl from '../../backend';
import ALERT_SETTINGS from './constants';


const reset = createAction(
  ALERT_SETTINGS,
  () => ({ status: 'initial' })
);


export const begin = createAction(
  ALERT_SETTINGS,
  () => ({ status: 'pending' })
);


const success = createAction(
  ALERT_SETTINGS,
  response => ({
    response,
    status: 'success',
  })
);


const fail = createAction(
  ALERT_SETTINGS,
  error => ({
    status: 'error',
    error,
  })
);


const get = () =>
  (dispatch) => {
    dispatch(begin());
    const url = `${apiUrl}/notifications`;
    fetch({ url })
      .then(response => {
        dispatch(success(response));
        return response;
      })
      .catch(error => {
        dispatch(fail(error.message));
      });
  };

const actions = {
  reset,
  begin,
  success,
  fail,
  get,
};

export default actions;
