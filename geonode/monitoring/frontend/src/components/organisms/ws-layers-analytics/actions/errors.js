import { createAction } from 'redux-actions';
import { fetch } from '../../../../utils';
import apiUrl from '../../../../backend';
import { WS_LAYER_ERROR } from '../constants';


const reset = createAction(
  WS_LAYER_ERROR,
  () => ({ status: 'initial' })
);


export const begin = createAction(
  WS_LAYER_ERROR,
  () => ({ status: 'pending' })
);


const success = createAction(
  WS_LAYER_ERROR,
  response => ({
    response,
    status: 'success',
  })
);


const fail = createAction(
  WS_LAYER_ERROR,
  error => ({
    status: 'error',
    error,
  })
);


const get = (interval, layer, owsService) =>
  (dispatch) => {
    dispatch(begin());
    const url = `${apiUrl}/metric_data/response.error.count/?last=${interval}&interval=${interval}`;
    fetch({ url: `${url}&resource=${layer}&ows_service=${owsService}` })
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
  get,
};
