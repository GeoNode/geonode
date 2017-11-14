import { createAction } from 'redux-actions';
import { fetch } from '../../../utils';
import apiUrl from '../../../backend';
import ERROR_DETAIL from './constants';


const reset = createAction(
  ERROR_DETAIL,
  () => ({ status: 'initial' })
);


export const begin = createAction(
  ERROR_DETAIL,
  () => ({ status: 'pending' })
);


const success = createAction(
  ERROR_DETAIL,
  response => ({
    response,
    status: 'success',
  })
);


const fail = createAction(
  ERROR_DETAIL,
  error => ({
    status: 'error',
    error,
  })
);


const get = (errorId) =>
  (dispatch) => {
    dispatch(begin());
    const url = `${apiUrl}/exceptions/${errorId}`;
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
