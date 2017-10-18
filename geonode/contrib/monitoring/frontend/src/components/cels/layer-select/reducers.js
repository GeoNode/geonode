import LAYER_LIST from './constants';

export default function layerList(
  state = { status: 'initial' },
  action,
) {
  switch (action.type) {
    case LAYER_LIST:
      return action.payload;
    default:
      return state;
  }
}
