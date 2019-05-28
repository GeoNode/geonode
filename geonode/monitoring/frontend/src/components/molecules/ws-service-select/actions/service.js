import { createAction } from 'redux-actions';
import { WS_SERVICE } from '../constants';


const reset = createAction(
  WS_SERVICE,
  () => ({ status: 'initial' })
);


const set = createAction(
  WS_SERVICE,
  service => ({
    service,
    status: 'success',
  })
);


const actions = {
  reset,
  set,
};

export default actions;
