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


const get = () =>
  (dispatch) => {
    dispatch(begin());
    fetch({
      url: `${apiUrl}/metric_data/response.time/?valid_from=2017-06-26`,
    })
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
