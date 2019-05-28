import { GEOSERVER_CPU_SEQUENCE, GEOSERVER_MEMORY_SEQUENCE } from './constants';


export function geoserverCpuSequence(
  state = { status: 'initial' },
  action,
) {
  switch (action.type) {
    case GEOSERVER_CPU_SEQUENCE:
      return action.payload;
    default:
      return state;
  }
}


export function geoserverMemorySequence(
  state = { status: 'initial' },
  action,
) {
  switch (action.type) {
    case GEOSERVER_MEMORY_SEQUENCE:
      return action.payload;
    default:
      return state;
  }
}
