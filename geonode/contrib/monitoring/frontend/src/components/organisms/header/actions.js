import { createAction } from 'redux-actions';
import { formatNow } from '../../../utils';
import { INTERVAL } from './constants';
import { minute } from '../../../constants';


const resetInterval = createAction(INTERVAL, () => ({ interval: 10 * minute }));


const setInterval = createAction(
  INTERVAL,
  (interval) => ({
    interval,
    timestamp: formatNow(),
  }),
);


export default {
  setInterval,
  resetInterval,
};
