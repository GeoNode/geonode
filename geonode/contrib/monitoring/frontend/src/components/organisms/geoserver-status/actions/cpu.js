import { createAction } from 'redux-actions';
import { fetch, sequenceInterval } from '../../../../utils';
import apiUrl from '../../../../backend';
import { GEOSERVER_CPU_SEQUENCE } from '../constants';


const reset = createAction(
  GEOSERVER_CPU_SEQUENCE,
  () => ({ status: 'initial' })
);


export const begin = createAction(
  GEOSERVER_CPU_SEQUENCE,
  () => ({ status: 'pending' })
);


const success = createAction(
  GEOSERVER_CPU_SEQUENCE,
  response => ({
    response,
    status: 'success',
  })
);


const fail = createAction(
  GEOSERVER_CPU_SEQUENCE,
  error => ({
    status: 'error',
    error,
  })
);


const get = (host, argInterval) =>
  (dispatch) => {
    dispatch(begin());
    const interval = sequenceInterval(argInterval);
    let url = `${apiUrl}/metric_data/cpu.usage.percent/?last=${argInterval}&interval=${interval}`;
    url += `&service=${host}`;
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
