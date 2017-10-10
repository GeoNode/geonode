import { createAction } from 'redux-actions';
import { fetch } from '../../../../utils';
import apiUrl from '../../../../backend';
import { GEONODE_MEM_STATUS } from '../constants';


const reset = createAction(
  GEONODE_MEM_STATUS,
  () => ({ status: 'initial' })
);


export const begin = createAction(
  GEONODE_MEM_STATUS,
  () => ({ status: 'pending' })
);


const success = createAction(
  GEONODE_MEM_STATUS,
  response => ({
    response,
    status: 'success',
  })
);


const fail = createAction(
  GEONODE_MEM_STATUS,
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
