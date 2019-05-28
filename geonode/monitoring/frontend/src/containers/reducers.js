import { THEME } from './constants';
import themes from '../themes';


export default function theme(
  state = { open: false, theme: themes.light },
  action
) {
  switch (action.type) {
    case THEME:
      return action.payload;
    default:
      return state;
  }
}
