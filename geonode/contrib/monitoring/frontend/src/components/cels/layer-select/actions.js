import { createAction } from 'redux-actions';
import { fetch } from '../../../utils';
import apiUrl from '../../../backend';
import LAYER_LIST from './constants';


const reset = createAction(
  LAYER_LIST,
  () => ({ status: 'initial' })
);


export const begin = createAction(
  LAYER_LIST,
  () => ({ status: 'pending' })
);


const success = createAction(
  LAYER_LIST,
  response => ({
    response: response.resources,
    status: 'success',
  })
);


const fail = createAction(
  LAYER_LIST,
  error => ({
    status: 'error',
    error,
  })
);


const get = () =>
  (dispatch) => {
    dispatch(begin());
    const url = `${apiUrl}/resources/?resource_type=layer`;
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
