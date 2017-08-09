import { combineReducers } from 'redux';
import theme from './containers/reducers';
import { backend, notifications } from './containers/app/reducers';
import geonodeAverageResponse from './components/cels/geonode-data/reducers';
import { geonodeCpuStatus, geonodeMemStatus } from './components/cels/geonode-status/reducers';
import { geoserverCpuStatus } from './components/cels/geoserver-status/reducers';
import { geoserverMemStatus } from './components/cels/geoserver-status/reducers';
import { geonodeResponseSequence } from './components/organisms/geonode-analytics/reducers';
import { geonodeThroughputSequence } from './components/organisms/geonode-analytics/reducers';
import { geonodeErrorSequence } from './components/organisms/geonode-analytics/reducers';
import { geonodeCpuSequence } from './components/organisms/geonode-status/reducers';
import { geonodeMemorySequence } from './components/organisms/geonode-status/reducers';
import { interval } from './components/organisms/header/reducers';
import { wsService, wsServices } from './components/molecules/ws-service-select/reducers';
import wsServiceData from './components/cels/ws-data/reducers';
import { wsResponseSequence } from './components/organisms/ws-analytics/reducers';
import { wsThroughputSequence } from './components/organisms/ws-analytics/reducers';
import { wsErrorSequence } from './components/organisms/ws-analytics/reducers';
import errorList from './components/organisms/error-list/reducers';
import errorDetails from './components/organisms/error-detail/reducers';
import uptime from './components/cels/uptime/reducers';


const reducers = {
  backend,
  errorDetails,
  errorList,
  geonodeAverageResponse,
  geonodeCpuSequence,
  geonodeCpuStatus,
  geonodeErrorSequence,
  geonodeMemStatus,
  geonodeMemorySequence,
  geonodeResponseSequence,
  geonodeThroughputSequence,
  geoserverCpuStatus,
  geoserverMemStatus,
  interval,
  notifications,
  theme,
  uptime,
  wsErrorSequence,
  wsResponseSequence,
  wsService,
  wsServiceData,
  wsServices,
  wsThroughputSequence,
};


const rootReducer = combineReducers(reducers);

export default rootReducer;
