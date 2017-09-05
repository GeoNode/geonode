import { createAction } from 'redux-actions';
import { fetch } from '../../utils';
import apiUrl from '../../backend';
import ALERT_CONFIG from './constants';


const reset = createAction(
  ALERT_CONFIG,
  () => ({ status: 'initial' })
);


export const begin = createAction(
  ALERT_CONFIG,
  () => ({ status: 'pending' })
);


const success = createAction(
  ALERT_CONFIG,
  response => ({
    response,
    status: 'success',
  })
);


const fail = createAction(
  ALERT_CONFIG,
  error => ({
    status: 'error',
    error,
  })
);


const get = (id) =>
  (dispatch) => {
    dispatch(begin());
    const url = `${apiUrl}/notifications/config/${id}`;
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
