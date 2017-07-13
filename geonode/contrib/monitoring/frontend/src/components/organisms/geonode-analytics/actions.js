import { createAction } from 'redux-actions';
import { fetch, formatApiDate } from '../../../utils';
import apiUrl from '../../../backend';
import GEONODE_RESPONSE_SEQUENCE from './constants';


const reset = createAction(
  GEONODE_RESPONSE_SEQUENCE,
  () => ({ status: 'initial' })
);


export const begin = createAction(
  GEONODE_RESPONSE_SEQUENCE,
  () => ({ status: 'pending' })
);


const success = createAction(
  GEONODE_RESPONSE_SEQUENCE,
  response => ({
    response,
    status: 'success',
  })
);


const fail = createAction(
  GEONODE_RESPONSE_SEQUENCE,
  error => ({
    status: 'error',
    error,
  })
);


const get = (from, to) =>
  (dispatch) => {
    dispatch(begin());
    const formatedFrom = formatApiDate(from);
    const formatedTo = formatApiDate(to);
    let url = `${apiUrl}/metric_data/response.time/?valid_from=${formatedFrom}`;
    url += `&valid_to=${formatedTo}`;
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
