import { createAction } from 'redux-actions';
import { fetch, sequenceInterval } from '../../../../utils';
import apiUrl from '../../../../backend';
import { GEONODE_CPU_SEQUENCE } from '../constants';


const reset = createAction(
  GEONODE_CPU_SEQUENCE,
  () => ({ status: 'initial' })
);


export const begin = createAction(
  GEONODE_CPU_SEQUENCE,
  () => ({ status: 'pending' })
);


const success = createAction(
  GEONODE_CPU_SEQUENCE,
  response => ({
    response,
    status: 'success',
  })
);


const fail = createAction(
  GEONODE_CPU_SEQUENCE,
  error => ({
    status: 'error',
    error,
  })
);


const get = (host, argInterval) =>
  (dispatch) => {
    dispatch(begin());
    const interval = sequenceInterval(argInterval);
    let url = `${apiUrl}/metric_data/cpu.usage.percent/?last=${argInterval}`;
    url += `&interval=${interval}&service=${host}`;
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
