import { createAction } from 'redux-actions';
import { fetch } from '../../../utils';
import apiUrl from '../../../backend';
import ALERT_LIST from './constants';


const reset = createAction(
  ALERT_LIST,
  () => ({ status: 'initial' })
);


export const begin = createAction(
  ALERT_LIST,
  () => ({ status: 'pending' })
);


const success = createAction(
  ALERT_LIST,
  response => ({
    response,
    status: 'success',
  })
);


const fail = createAction(
  ALERT_LIST,
  error => ({
    status: 'error',
    error,
  })
);


const get = (interval) =>
  (dispatch) => {
    dispatch(begin());
    const url = `${apiUrl}/status/?last=${interval}`;
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
