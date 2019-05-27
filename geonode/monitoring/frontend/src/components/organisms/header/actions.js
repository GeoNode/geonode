import { createAction } from 'redux-actions';
import { fetch, formatNow } from '../../../utils';
import apiUrl from '../../../backend';
import { INTERVAL } from './constants';
import { minute } from '../../../constants';


const reset = createAction(INTERVAL, () => ({ interval: 10 * minute }));


export const begin = createAction(
  INTERVAL,
  (interval) => ({
    interval,
    status: 'pending',
  })
);


const success = createAction(
  INTERVAL,
  (interval, response) => ({
    interval,
    from: new Date(response.data.input_valid_from),
    to: new Date(response.data.input_valid_to),
    timestamp: formatNow(),
    status: 'success',
  }),
);


const fail = createAction(
  INTERVAL,
  error => ({
    status: 'error',
    error,
  })
);


const get = (interval) =>
  (dispatch) => {
    dispatch(begin(interval));
    const url = `${apiUrl}/metric_data/response.error.count/?last=${interval}&interval=${interval}`;
    fetch({ url })
      .then(response => {
        dispatch(success(interval, response));
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
