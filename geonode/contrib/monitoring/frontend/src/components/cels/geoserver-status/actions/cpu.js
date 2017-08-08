import { createAction } from 'redux-actions';
import { fetch, formatApiDate } from '../../../../utils';
import apiUrl from '../../../../backend';
import { GEOSERVER_CPU_STATUS } from '../constants';


const reset = createAction(
  GEOSERVER_CPU_STATUS,
  () => ({ status: 'initial' })
);


export const begin = createAction(
  GEOSERVER_CPU_STATUS,
  () => ({ status: 'pending' })
);


const success = createAction(
  GEOSERVER_CPU_STATUS,
  response => ({
    response,
    status: 'success',
  })
);


const fail = createAction(
  GEOSERVER_CPU_STATUS,
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
    let url = `${apiUrl}/metric_data/cpu.usage.percent/?valid_from=${formatedFrom}`;
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
