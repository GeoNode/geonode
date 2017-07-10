import GEONODE_STATUS from './constants';

export default function geonodeStatus(
  state = { status: 'initial' },
  action,
) {
  switch (action.type) {
    case GEONODE_STATUS:
      return action.payload;
    default:
      return state;
  }
}
