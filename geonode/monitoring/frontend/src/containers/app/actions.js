import { createAction } from 'redux-actions';
import { fetch } from '../../utils';
import apiUrl from '../../backend';
import SERVICES from './constants';


const reset = createAction(
  SERVICES,
  () => ({ status: 'initial' })
);


export const begin = createAction(
  SERVICES,
  () => ({ status: 'pending' })
);


const success = createAction(
  SERVICES,
  response => ({
    ...response,
    status: 'success',
  })
);


const fail = createAction(
  SERVICES,
  error => ({
    status: 'error',
    error,
  })
);


const get = () =>
  (dispatch) => {
    dispatch(begin());
    const url = `${apiUrl}/services`;
    fetch({ url })
      .then(response => {
        const result = {};
        response.services.forEach((service) => {
          if (!result[service.type]) {
            result[service.type] = [];
          }
          result[service.type].push(service);
        });
        dispatch(success(result));
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
