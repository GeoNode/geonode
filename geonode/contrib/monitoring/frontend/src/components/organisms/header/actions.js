import { createAction } from 'redux-actions';
import INTERVAL, { minute } from './constants';


const reset = createAction(INTERVAL, () => ({ interval: 10 * minute }));


const set = createAction(
  INTERVAL,
  (from, to, interval) => ({ from, to, interval }),
);


export default {
  reset,
  set,
};
