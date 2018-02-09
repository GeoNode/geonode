import { createAction } from 'redux-actions';
import { fetch } from '../../../utils';
import apiUrl from '../../../backend';
import UPTIME from './constants';


const reset = createAction(
  UPTIME,
  () => ({ status: 'initial' })
);


export const begin = createAction(
  UPTIME,
  () => ({ status: 'pending' })
);


const success = createAction(
  UPTIME,
  response => ({
    response,
    status: 'success',
  })
);


const fail = createAction(
  UPTIME,
  error => ({
    status: 'error',
    error,
  })
);


const get = () =>
  (dispatch) => {
    dispatch(begin());
    const url = `${apiUrl}/metric_data/uptime`;
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
