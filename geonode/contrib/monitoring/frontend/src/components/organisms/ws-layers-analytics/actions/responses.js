import { createAction } from 'redux-actions';
import { fetch } from '../../../../utils';
import apiUrl from '../../../../backend';
import { WS_LAYER_RESPONSE } from '../constants';


const reset = createAction(
  WS_LAYER_RESPONSE,
  () => ({ status: 'initial' })
);


export const begin = createAction(
  WS_LAYER_RESPONSE,
  () => ({ status: 'pending' })
);


const success = createAction(
  WS_LAYER_RESPONSE,
  response => ({
    response,
    status: 'success',
  })
);


const fail = createAction(
  WS_LAYER_RESPONSE,
  error => ({
    status: 'error',
    error,
  })
);


const get = (interval) =>
  (dispatch) => {
    dispatch(begin());
    const url = `${apiUrl}/metric_data/response.time/?last=${interval}&interval=${interval}`;
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
