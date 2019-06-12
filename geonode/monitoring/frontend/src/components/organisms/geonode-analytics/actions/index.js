import responses from './responses';
import throughput from './throughput';
import error from './error';
import responseTimes from '../../../cels/geonode-data/actions';


export default {
  getResponses: responses.get,
  resetResponses: responses.reset,
  getResponseTimes: responseTimes.get,
  resetResponseTimes: responseTimes.reset,
  getThroughputs: throughput.get,
  resetThroughputs: throughput.reset,
  getErrors: error.get,
  resetErrors: error.reset,
};
