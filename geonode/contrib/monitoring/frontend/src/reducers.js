import { combineReducers } from 'redux';
import theme from './containers/reducers';
import { services } from './containers/app/reducers';

// Atoms
import mapData from './components/atoms/map/reducers';

// Molecules
import { wsService, wsServices } from './components/molecules/ws-service-select/reducers';

// Cels
import frequentLayers from './components/cels/frequent-layers/reducers';
import geonodeAverageResponse from './components/cels/geonode-data/reducers';
import layerList from './components/cels/layer-select/reducers';
import uptime from './components/cels/uptime/reducers';
import wsServiceData from './components/cels/ws-data/reducers';
import { geonodeCpuStatus, geonodeMemStatus } from './components/cels/geonode-status/reducers';
import { geoserverCpuStatus } from './components/cels/geoserver-status/reducers';
import { geoserverMemStatus } from './components/cels/geoserver-status/reducers';

// Organisms
import alertList from './components/organisms/alert-list/reducers';
import errorDetails from './components/organisms/error-detail/reducers';
import errorList from './components/organisms/error-list/reducers';
import { geonodeCpuSequence } from './components/organisms/geonode-status/reducers';
import { geonodeErrorSequence } from './components/organisms/geonode-analytics/reducers';
import { geonodeLayerError } from './components/organisms/geonode-layers-analytics/reducers';
import { geonodeLayerResponse } from './components/organisms/geonode-layers-analytics/reducers';
import { geonodeMemorySequence } from './components/organisms/geonode-status/reducers';
import { geonodeResponseSequence } from './components/organisms/geonode-analytics/reducers';
import { geonodeThroughputSequence } from './components/organisms/geonode-analytics/reducers';
import { geoserverCpuSequence } from './components/organisms/geoserver-status/reducers';
import { geoserverMemorySequence } from './components/organisms/geoserver-status/reducers';
import { interval } from './components/organisms/header/reducers';
import { wsErrorSequence } from './components/organisms/ws-analytics/reducers';
import { wsLayerError } from './components/organisms/ws-layers-analytics/reducers';
import { wsLayerResponse } from './components/organisms/ws-layers-analytics/reducers';
import { wsResponseSequence } from './components/organisms/ws-analytics/reducers';
import { wsThroughputSequence } from './components/organisms/ws-analytics/reducers';

// Pages
import { alertConfig, alertConfigSave } from './pages/alert-config/reducers';
import alertSettings from './pages/alerts-settings/reducers';


const reducers = {
  alertConfig,
  alertConfigSave,
  alertList,
  alertSettings,
  errorDetails,
  errorList,
  frequentLayers,
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
  geoserverMemStatus,
  geoserverMemorySequence,
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


export default combineReducers(reducers);
