import ERROR_DETAIL from './constants';


export default function errorDetails(
  state = { status: 'initial' },
  action,
) {
  switch (action.type) {
    case ERROR_DETAIL:
      return action.payload;
    default:
      return state;
  }
}
