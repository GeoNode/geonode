import { createAction } from 'redux-actions';
import { fetch, formatApiDate, sequenceInterval } from '../../../../utils';
import apiUrl from '../../../../backend';
import { WS_RESPONSE_SEQUENCE } from '../constants';


const reset = createAction(
  WS_RESPONSE_SEQUENCE,
  () => ({ status: 'initial' })
);


export const begin = createAction(
  WS_RESPONSE_SEQUENCE,
  () => ({ status: 'pending' })
);


const success = createAction(
  WS_RESPONSE_SEQUENCE,
  response => ({
    response,
    status: 'success',
  })
);


const fail = createAction(
  WS_RESPONSE_SEQUENCE,
  error => ({
    status: 'error',
    error,
  })
);


const get = (from, to) =>
  (dispatch, getState) => {
    dispatch(begin());
    const formatedFrom = formatApiDate(from);
    const formatedTo = formatApiDate(to);
    const interval = sequenceInterval(getState);
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
