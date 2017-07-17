import { createAction } from 'redux-actions';
import { INTERVAL, AUTO_REFRESH } from './constants';
import { minute } from '../../../constants';


const resetInterval = createAction(INTERVAL, () => ({ interval: 10 * minute }));


const setInterval = createAction(
  INTERVAL,
  (from, to, interval) => ({ from, to, interval }),
);


const resetAutoRefresh = createAction(AUTO_REFRESH, () => ({ state: 'initial' }));


const setAutoRefresh = createAction(AUTO_REFRESH, (autoRefresh) => (autoRefresh));


export default {
  resetAutoRefresh,
  resetInterval,
  setAutoRefresh,
  setInterval,
};
