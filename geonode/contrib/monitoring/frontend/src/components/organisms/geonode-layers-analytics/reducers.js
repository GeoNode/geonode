import { GEONODE_LAYER_ERROR, GEONODE_LAYER_RESPONSE } from './constants';


export function geonodeLayerResponse(
  state = { status: 'initial' },
  action,
) {
  switch (action.type) {
    case GEONODE_LAYER_RESPONSE:
      return action.payload;
    default:
      return state;
  }
}


export function geonodeLayerError(
  state = { status: 'initial' },
  action,
) {
  switch (action.type) {
    case GEONODE_LAYER_ERROR:
      return action.payload;
    default:
      return state;
  }
}
