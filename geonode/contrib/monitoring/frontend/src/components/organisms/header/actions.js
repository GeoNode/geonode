import { createAction } from 'redux-actions';
import INTERVAL, { minute } from './constants';
import formatDate from './utils';


const reset = createAction(INTERVAL, () => ({ interval: 10 * minute }));


const set = createAction(
  INTERVAL,
  (from, to, interval) => ({
    from: formatDate(from),
    to: formatDate(to),
    interval,
  }),
);


export default {
  reset,
  set,
};
