import { createAction } from 'redux-actions';
import { fetch, formatApiDate } from '../../../utils';
import apiUrl from '../../../backend';
import WS_SERVICE_DATA from './constants';


const reset = createAction(
  WS_SERVICE_DATA,
  () => ({ status: 'initial' })
);


export const begin = createAction(
  WS_SERVICE_DATA,
  () => ({ status: 'pending' })
);


const success = createAction(
  WS_SERVICE_DATA,
  response => ({
    response,
    status: 'success',
  })
);


const fail = createAction(
  WS_SERVICE_DATA,
  error => ({
    status: 'error',
    error,
  })
);


const get = (from, to, interval, service) =>
  (dispatch) => {
    dispatch(begin());
    const formatedFrom = formatApiDate(from);
    const formatedTo = formatApiDate(to);
    let url = `${apiUrl}/metric_data/response.time/?valid_from=${formatedFrom}`;
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

const actions = {
  reset,
  begin,
  success,
  fail,
  get,
};

export default actions;
