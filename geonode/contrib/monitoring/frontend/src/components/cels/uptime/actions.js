import { createAction } from 'redux-actions';
import { fetch, formatApiDate } from '../../../utils';
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


const get = (from, to, interval) =>
  (dispatch) => {
    dispatch(begin());
    const formatedFrom = formatApiDate(from);
    const formatedTo = formatApiDate(to);
    let url = `${apiUrl}/metric_data/uptime/?valid_from=${formatedFrom}`;
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
