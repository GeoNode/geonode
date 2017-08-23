import { createAction } from 'redux-actions';
import { fetch } from '../../../utils';
import apiUrl from '../../../backend';
import ERROR_LIST from './constants';


const reset = createAction(
  ERROR_LIST,
  () => ({ status: 'initial' })
);


export const begin = createAction(
  ERROR_LIST,
  () => ({ status: 'pending' })
);


const success = createAction(
  ERROR_LIST,
  response => ({
    response,
    status: 'success',
  })
);


const fail = createAction(
  ERROR_LIST,
  error => ({
    status: 'error',
    error,
  })
);


const get = (interval) =>
  (dispatch) => {
    dispatch(begin());
    const url = `${apiUrl}/exceptions/?last=${interval}&interval=${interval}`;
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
