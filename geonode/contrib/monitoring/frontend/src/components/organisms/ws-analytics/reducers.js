import { WS_RESPONSE_SEQUENCE } from './constants';
import { WS_THROUGHPUT_SEQUENCE } from './constants';
import { WS_ERROR_SEQUENCE } from './constants';


export function wsResponseSequence(
  state = { status: 'initial' },
  action,
) {
  switch (action.type) {
    case WS_RESPONSE_SEQUENCE:
      return action.payload;
    default:
      return state;
  }
}


export function wsThroughputSequence(
  state = { status: 'initial' },
  action,
) {
  switch (action.type) {
    case WS_THROUGHPUT_SEQUENCE:
      return action.payload;
    default:
      return state;
  }
}


export function wsErrorSequence(
  state = { status: 'initial' },
  action,
) {
  switch (action.type) {
    case WS_ERROR_SEQUENCE:
      return action.payload;
    default:
      return state;
  }
}
