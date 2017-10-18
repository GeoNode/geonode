import { GEONODE_CPU_STATUS, GEONODE_MEM_STATUS } from './constants';

export function geonodeCpuStatus(
  state = { status: 'initial' },
  action,
) {
  switch (action.type) {
    case GEONODE_CPU_STATUS:
      return action.payload;
    default:
      return state;
  }
}


export function geonodeMemStatus(
  state = { status: 'initial' },
  action,
) {
  switch (action.type) {
    case GEONODE_MEM_STATUS:
      return action.payload;
    default:
      return state;
  }
}
