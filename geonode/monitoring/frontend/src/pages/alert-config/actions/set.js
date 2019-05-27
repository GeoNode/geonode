import { createAction } from 'redux-actions';
import { fetch } from '../../../utils';
import apiUrl from '../../../backend';
import { ALERT_CONFIG_SET } from '../constants';


const reset = createAction(
  ALERT_CONFIG_SET,
  () => ({ status: 'initial' })
);


export const begin = createAction(
  ALERT_CONFIG_SET,
  () => ({ status: 'pending' })
);


const success = createAction(
  ALERT_CONFIG_SET,
  response => ({
    response,
    status: 'success',
  })
);


const fail = createAction(
  ALERT_CONFIG_SET,
  error => ({
    status: 'error',
    error,
  })
);


const set = (id, data) =>
  (dispatch) => {
    dispatch(begin());
    const url = `${apiUrl}/notifications/config/${id}/`;
    fetch({ url, body: data, method: 'POST' })
      .then(response => {
        dispatch(success(response));
        return response;
      })
      .catch(error => {
        dispatch(fail(error.message));
      });
  };


export default {
  reset,
  begin,
  success,
  fail,
  set,
};
