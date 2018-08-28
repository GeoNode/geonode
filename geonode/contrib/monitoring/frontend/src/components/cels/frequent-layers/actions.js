import { createAction } from 'redux-actions';
import { fetch } from '../../../utils';
import apiUrl from '../../../backend';
import FREQUENT_LAYERS from './constants';


const reset = createAction(
  FREQUENT_LAYERS,
  () => ({ status: 'initial' })
);


export const begin = createAction(
  FREQUENT_LAYERS,
  () => ({ status: 'pending' })
);


const success = createAction(
  FREQUENT_LAYERS,
  response => ({
    response,
    status: 'success',
  })
);


const fail = createAction(
  FREQUENT_LAYERS,
  error => ({
    status: 'error',
    error,
  })
);


const get = (interval) =>
  (dispatch) => {
    dispatch(begin());
    let url = `${apiUrl}/metric_data/request.count/?group_by=resource`;
    url += `&resource_type=layer&last=${interval}&interval=${interval}`;
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
