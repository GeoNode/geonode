import ERROR_LIST from './constants';


export default function errorList(
  state = { status: 'initial' },
  action,
) {
  switch (action.type) {
    case ERROR_LIST:
      return action.payload;
    default:
      return state;
  }
}
