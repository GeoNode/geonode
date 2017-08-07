import WS_SERVICE_DATA from './constants';


export default function wsServiceData(
  state = { status: 'initial' },
  action,
) {
  switch (action.type) {
    case WS_SERVICE_DATA:
      return action.payload;
    default:
      return state;
  }
}
