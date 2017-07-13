import GEONODE_RESPONSE_SEQUENCE from './constants';

export default function geonodeResponseSequence(
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
