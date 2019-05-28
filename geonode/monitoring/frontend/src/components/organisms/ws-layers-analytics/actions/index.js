import responses from './responses';
import errors from './errors';


export default {
  getResponses: responses.get,
  resetResponses: responses.reset,
  getErrors: errors.get,
  resetErrors: errors.reset,
};
