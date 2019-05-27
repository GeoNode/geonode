import { GEONODE_RESPONSE_SEQUENCE } from './constants';
import { GEONODE_THROUGHPUT_SEQUENCE } from './constants';
import { GEONODE_ERROR_SEQUENCE } from './constants';


export function geonodeResponseSequence(
  state = { status: 'initial' },
  action,
) {
  switch (action.type) {
    case GEONODE_RESPONSE_SEQUENCE:
      return action.payload;
    default:
      return state;
  }
}


export function geonodeThroughputSequence(
  state = { status: 'initial' },
  action,
) {
  switch (action.type) {
    case GEONODE_THROUGHPUT_SEQUENCE:
      return action.payload;
    default:
      return state;
  }
}


export function geonodeErrorSequence(
  state = { status: 'initial' },
  action,
) {
  switch (action.type) {
    case GEONODE_ERROR_SEQUENCE:
      return action.payload;
    default:
      return state;
  }
}
