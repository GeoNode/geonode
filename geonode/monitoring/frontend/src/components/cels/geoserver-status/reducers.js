import { GEOSERVER_CPU_STATUS, GEOSERVER_MEM_STATUS } from './constants';

export function geoserverCpuStatus(
  state = { status: 'initial' },
  action,
) {
  switch (action.type) {
    case GEOSERVER_CPU_STATUS:
      return action.payload;
    default:
      return state;
  }
}


export function geoserverMemStatus(
  state = { status: 'initial' },
  action,
) {
  switch (action.type) {
    case GEOSERVER_MEM_STATUS:
      return action.payload;
    default:
      return state;
  }
}
