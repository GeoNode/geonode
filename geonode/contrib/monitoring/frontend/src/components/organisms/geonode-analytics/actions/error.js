import { createAction } from 'redux-actions';
import { fetch, sequenceInterval } from '../../../../utils';
import apiUrl from '../../../../backend';
import { GEONODE_ERROR_SEQUENCE } from '../constants';


const reset = createAction(
  GEONODE_ERROR_SEQUENCE,
  () => ({ status: 'initial' })
);


export const begin = createAction(
  GEONODE_ERROR_SEQUENCE,
  () => ({ status: 'pending' })
);


const success = createAction(
  GEONODE_ERROR_SEQUENCE,
  response => ({
    response,
    status: 'success',
  })
);


const fail = createAction(
  GEONODE_ERROR_SEQUENCE,
  error => ({
    status: 'error',
    error,
  })
);


const get = (argInterval) =>
  (dispatch) => {
    dispatch(begin());
    const interval = sequenceInterval(argInterval);
    let url = `${apiUrl}/metric_data/response.error.count/`;
    url += `?last=${argInterval}&interval=${interval}`;
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
