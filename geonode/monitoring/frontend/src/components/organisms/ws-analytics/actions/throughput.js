import { createAction } from 'redux-actions';
import { fetch, sequenceInterval } from '../../../../utils';
import apiUrl from '../../../../backend';
import { WS_THROUGHPUT_SEQUENCE } from '../constants';


const reset = createAction(
  WS_THROUGHPUT_SEQUENCE,
  () => ({ status: 'initial' })
);


export const begin = createAction(
  WS_THROUGHPUT_SEQUENCE,
  () => ({ status: 'pending' })
);


const success = createAction(
  WS_THROUGHPUT_SEQUENCE,
  throughput => ({
    throughput,
    status: 'success',
  })
);


const fail = createAction(
  WS_THROUGHPUT_SEQUENCE,
  error => ({
    status: 'error',
    error,
  })
);


const get = (service, argInterval) =>
  (dispatch) => {
    dispatch(begin());
    const interval = sequenceInterval(argInterval);
    let url = `${apiUrl}/metric_data/request.count/?ows_service=${service}`;
    url += `&last=${argInterval}&interval=${interval}`;
    fetch({ url })
      .then(throughput => {
        dispatch(success(throughput));
        return throughput;
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
