import { createAction } from 'redux-actions';
import { fetch } from '../../../../utils';
import apiUrl from '../../../../backend';
import { GEOSERVER_MEM_STATUS } from '../constants';


const reset = createAction(
  GEOSERVER_MEM_STATUS,
  () => ({ status: 'initial' })
);


export const begin = createAction(
  GEOSERVER_MEM_STATUS,
  () => ({ status: 'pending' })
);


const success = createAction(
  GEOSERVER_MEM_STATUS,
  response => ({
    response,
    status: 'success',
  })
);


const fail = createAction(
  GEOSERVER_MEM_STATUS,
  error => ({
    status: 'error',
    error,
  })
);


const get = (host, interval) =>
  (dispatch) => {
    dispatch(begin());
    let url = `${apiUrl}/metric_data/mem.free/?service=${host}`;
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
