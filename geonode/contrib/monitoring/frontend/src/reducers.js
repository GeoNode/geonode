import { combineReducers } from 'redux';
import theme from './containers/reducers';
import { services } from './containers/app/reducers';

// Atoms
import mapData from './components/atoms/map/reducers';

// Molecules
import { wsService, wsServices } from './components/molecules/ws-service-select/reducers';

// Cels
import uptime from './components/cels/uptime/reducers';
import geonodeAverageResponse from './components/cels/geonode-data/reducers';
import wsServiceData from './components/cels/ws-data/reducers';
import { geonodeCpuStatus, geonodeMemStatus } from './components/cels/geonode-status/reducers';
import { geoserverCpuStatus } from './components/cels/geoserver-status/reducers';
import { geoserverMemStatus } from './components/cels/geoserver-status/reducers';
import layerList from './components/cels/layer-select/reducers';

// Organisms
import { geonodeResponseSequence } from './components/organisms/geonode-analytics/reducers';
import { geonodeThroughputSequence } from './components/organisms/geonode-analytics/reducers';
import { geonodeErrorSequence } from './components/organisms/geonode-analytics/reducers';
import { geonodeCpuSequence } from './components/organisms/geonode-status/reducers';
import { geonodeMemorySequence } from './components/organisms/geonode-status/reducers';
import { geoserverCpuSequence } from './components/organisms/geoserver-status/reducers';
import { geoserverMemorySequence } from './components/organisms/geoserver-status/reducers';
import { interval } from './components/organisms/header/reducers';
import { wsResponseSequence } from './components/organisms/ws-analytics/reducers';
import { wsThroughputSequence } from './components/organisms/ws-analytics/reducers';
import { wsErrorSequence } from './components/organisms/ws-analytics/reducers';
import errorList from './components/organisms/error-list/reducers';
import errorDetails from './components/organisms/error-detail/reducers';
import alertList from './components/organisms/alert-list/reducers';
import { geonodeLayerError } from './components/organisms/geonode-layers-analytics/reducers';
import { geonodeLayerResponse } from './components/organisms/geonode-layers-analytics/reducers';
import { wsLayerError } from './components/organisms/ws-layers-analytics/reducers';
import { wsLayerResponse } from './components/organisms/ws-layers-analytics/reducers';


const reducers = {
  alertList,
  errorDetails,
  errorList,
  geonodeAverageResponse,
  geonodeCpuSequence,
  geonodeCpuStatus,
  geonodeErrorSequence,
  geonodeLayerError,
  geonodeLayerResponse,
  geonodeMemStatus,
  geonodeMemorySequence,
  geonodeResponseSequence,
  geonodeThroughputSequence,
  geoserverCpuSequence,
  geoserverCpuStatus,
  geoserverMemorySequence,
  geoserverMemStatus,
  interval,
  layerList,
  mapData,
  services,
  theme,
  uptime,
  wsErrorSequence,
  wsLayerError,
  wsLayerResponse,
  wsResponseSequence,
  wsService,
  wsServiceData,
  wsServices,
  wsThroughputSequence,
};


const rootReducer = combineReducers(reducers);

export default rootReducer;
