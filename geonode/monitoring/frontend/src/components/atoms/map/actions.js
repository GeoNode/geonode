import { createAction } from 'redux-actions';
import { fetch } from '../../../utils';
import apiUrl from '../../../backend';
import MAP from './constants';


const reset = createAction(
  MAP,
  () => ({ status: 'initial' })
);


export const begin = createAction(
  MAP,
  () => ({ status: 'pending' })
);


const success = createAction(
  MAP,
  response => ({
    response,
    status: 'success',
  })
);


const fail = createAction(
  MAP,
  error => ({
    status: 'error',
    error,
  })
);


const get = (interval) =>
  (dispatch) => {
    dispatch(begin());
    const url = `${apiUrl}/metric_data/request.country/?last=${interval}&interval=${interval}`;
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
