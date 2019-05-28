import { WS_LAYER_ERROR, WS_LAYER_RESPONSE } from './constants';


export function wsLayerResponse(
  state = { status: 'initial' },
  action,
) {
  switch (action.type) {
    case WS_LAYER_RESPONSE:
      return action.payload;
    default:
      return state;
  }
}


export function wsLayerError(
  state = { status: 'initial' },
  action,
) {
  switch (action.type) {
    case WS_LAYER_ERROR:
      return action.payload;
    default:
      return state;
  }
}
