import responses from './responses';
import throughput from './throughput';
import error from './error';


export default {
  getResponses: responses.get,
  resetResponses: responses.reset,
  getThroughputs: throughput.get,
  resetThroughputs: throughput.reset,
  getErrors: error.get,
  resetErrors: error.reset,
};
