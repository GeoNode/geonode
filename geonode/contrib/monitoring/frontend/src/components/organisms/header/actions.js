import { createAction } from 'redux-actions';
import { INTERVAL } from './constants';
import { minute } from '../../../constants';


const resetInterval = createAction(INTERVAL, () => ({ interval: 10 * minute }));


const setInterval = createAction(
  INTERVAL,
  (from, to, interval) => ({ from, to, interval }),
);


export default {
  setInterval,
  resetInterval,
};
