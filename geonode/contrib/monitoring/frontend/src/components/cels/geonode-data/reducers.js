import GEONODE_AVERAGE_RESPONSE from './constants';

export default function geonodeAverageResponse(
  state = { status: 'initial' },
  action,
) {
  switch (action.type) {
    case GEONODE_AVERAGE_RESPONSE:
      return action.payload;
    default:
      return state;
  }
}
