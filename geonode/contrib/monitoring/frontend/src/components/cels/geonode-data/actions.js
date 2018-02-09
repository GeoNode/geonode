import { createAction } from 'redux-actions';
import { fetch } from '../../../utils';
import apiUrl from '../../../backend';
import GEONODE_AVERAGE_RESPONSE from './constants';


const reset = createAction(
  GEONODE_AVERAGE_RESPONSE,
  () => ({ status: 'initial' })
);


export const begin = createAction(
  GEONODE_AVERAGE_RESPONSE,
  () => ({ status: 'pending' })
);


const success = createAction(
  GEONODE_AVERAGE_RESPONSE,
  response => ({
    response,
    status: 'success',
  })
);


const fail = createAction(
  GEONODE_AVERAGE_RESPONSE,
  error => ({
    status: 'error',
    error,
  })
);


const get = (interval) =>
  (dispatch) => {
    dispatch(begin());
    let url = `${apiUrl}/metric_data/response.time/?service_type=geonode`;
    url += `&last=${interval}&interval=${interval}`;
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
