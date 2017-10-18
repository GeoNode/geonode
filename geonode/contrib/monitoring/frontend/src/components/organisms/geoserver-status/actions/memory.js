import { createAction } from 'redux-actions';
import { fetch, sequenceInterval } from '../../../../utils';
import apiUrl from '../../../../backend';
import { GEOSERVER_MEMORY_SEQUENCE } from '../constants';


const reset = createAction(
  GEOSERVER_MEMORY_SEQUENCE,
  () => ({ status: 'initial' })
);


export const begin = createAction(
  GEOSERVER_MEMORY_SEQUENCE,
  () => ({ status: 'pending' })
);


const success = createAction(
  GEOSERVER_MEMORY_SEQUENCE,
  response => ({
    response,
    status: 'success',
  })
);


const fail = createAction(
  GEOSERVER_MEMORY_SEQUENCE,
  error => ({
    status: 'error',
    error,
  })
);


const get = (host, argInterval) =>
  (dispatch) => {
    dispatch(begin());
    const interval = sequenceInterval(argInterval);
    let url = `${apiUrl}/metric_data/mem.usage.percent/?last=${argInterval}&interval=${interval}`;
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
