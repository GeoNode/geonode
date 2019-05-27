import { createAction } from 'redux-actions';
import { fetch } from '../../../../utils';
import apiUrl from '../../../../backend';
import { WS_SERVICES } from '../constants';


const reset = createAction(
  WS_SERVICES,
  () => ({ status: 'initial' })
);


export const begin = createAction(
  WS_SERVICES,
  () => ({ status: 'pending' })
);


const success = createAction(
  WS_SERVICES,
  response => ({
    response,
    status: 'success',
  })
);


const fail = createAction(
  WS_SERVICES,
  error => ({
    status: 'error',
    error,
  })
);


const get = () =>
  (dispatch) => {
    dispatch(begin());
    const url = `${apiUrl}/ows_services/`;
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
