import { formatNow } from '../../../utils';
import { INTERVAL } from './constants';
import { minute } from '../../../constants';


export function interval(
  state = {
    interval: 10 * minute,
    timestamp: formatNow(),
  },
  action,
) {
  switch (action.type) {
    case INTERVAL:
      return action.payload;
    default:
      return state;
  }
}
