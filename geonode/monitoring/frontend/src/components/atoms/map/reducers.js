import MAP from './constants';

export default function mapData(
  state = { status: 'initial' },
  action,
) {
  switch (action.type) {
    case MAP:
      return action.payload;
    default:
      return state;
  }
}
