import INTERVAL from './constants';
import { minute } from '../../../constants';


const rightNow = new Date();
rightNow.setSeconds(0, 0);


export default function interval(
  state = {
    from: new Date(rightNow - 10 * minute * 1000),
    interval: 10 * minute,
    to: rightNow,
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
