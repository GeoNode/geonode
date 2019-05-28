import { GEONODE_CPU_SEQUENCE, GEONODE_MEMORY_SEQUENCE } from './constants';


export function geonodeCpuSequence(
  state = { status: 'initial' },
  action,
) {
  switch (action.type) {
    case GEONODE_CPU_SEQUENCE:
      return action.payload;
    default:
      return state;
  }
}


export function geonodeMemorySequence(
  state = { status: 'initial' },
  action,
) {
  switch (action.type) {
    case GEONODE_MEMORY_SEQUENCE:
      return action.payload;
    default:
      return state;
  }
}
