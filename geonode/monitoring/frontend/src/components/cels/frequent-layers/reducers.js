import FREQUENT_LAYERS from './constants';

export default function frequentLayers(
  state = { status: 'initial' },
  action,
) {
  switch (action.type) {
    case FREQUENT_LAYERS:
      return action.payload;
    default:
      return state;
  }
}
