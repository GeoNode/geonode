import { createAction } from 'redux-actions';
import { fetch } from '../../../../utils';
import apiUrl from '../../../../backend';
import { GEONODE_LAYER_ERROR } from '../constants';


const reset = createAction(
  GEONODE_LAYER_ERROR,
  () => ({ status: 'initial' })
);


export const begin = createAction(
  GEONODE_LAYER_ERROR,
  () => ({ status: 'pending' })
);


const success = createAction(
  GEONODE_LAYER_ERROR,
  response => ({
    response,
    status: 'success',
  })
);


const fail = createAction(
  GEONODE_LAYER_ERROR,
  error => ({
    status: 'error',
    error,
  })
);


const get = (layer, interval) =>
  (dispatch) => {
    dispatch(begin());
    let url = `${apiUrl}/metric_data/response.error.count/?resource=${layer}`;
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

export default {
  reset,
  begin,
  success,
  fail,
  get,
};
