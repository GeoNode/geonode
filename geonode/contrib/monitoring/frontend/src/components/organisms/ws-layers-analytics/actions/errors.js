import { createAction } from 'redux-actions';
import { fetch, formatApiDate } from '../../../../utils';
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


const get = (from, to, interval) =>
  (dispatch) => {
    dispatch(begin());
    const formatedFrom = formatApiDate(from);
    const formatedTo = formatApiDate(to);
    let url = `${apiUrl}/metric_data/response.error.count/?valid_from=${formatedFrom}`;
    url += `&valid_to=${formatedTo}&interval=${interval}`;
    fetch({ url })
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
