import { createAction } from 'redux-actions';
import { fetch, sequenceInterval } from '../../../../utils';
import apiUrl from '../../../../backend';
import { GEONODE_THROUGHPUT_SEQUENCE } from '../constants';


const reset = createAction(
  GEONODE_THROUGHPUT_SEQUENCE,
  () => ({ status: 'initial' })
);


export const begin = createAction(
  GEONODE_THROUGHPUT_SEQUENCE,
  () => ({ status: 'pending' })
);


const success = createAction(
  GEONODE_THROUGHPUT_SEQUENCE,
  throughput => ({
    throughput,
    status: 'success',
  })
);


const fail = createAction(
  GEONODE_THROUGHPUT_SEQUENCE,
  error => ({
    status: 'error',
    error,
  })
);


const get = (argInterval) =>
  (dispatch) => {
    dispatch(begin());
    const interval = sequenceInterval(argInterval);
    const url = `${apiUrl}/metric_data/request.count/?last=${argInterval}&interval=${interval}`;
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
