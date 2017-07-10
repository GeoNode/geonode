import { createAction } from 'redux-actions';
import { fetch } from '../../../utils';
import apiUrl from '../../../backend';
import GEONODE_STATUS from './constants';
import { formatApiDate } from '../../../utils';


const reset = createAction(
  GEONODE_STATUS,
  () => ({ status: 'initial' })
);


export const begin = createAction(
  GEONODE_STATUS,
  () => ({ status: 'pending' })
);


const success = createAction(
  GEONODE_STATUS,
  response => ({
    response,
    status: 'success',
  })
);


const fail = createAction(
  GEONODE_STATUS,
  error => ({
    status: 'error',
    error,
  })
);


const get = (from, to, interval) =>
  (dispatch) => {
    dispatch(begin());
    const formatedFrom = formatApiDate(from);
    const formatedTo = formatApiDate(to);
    let url = `${apiUrl}/metric_data/cpu.usage/?valid_from=${formatedFrom}`;
    url += `&valid_to=${formatedTo}&interval=${interval}`;
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
