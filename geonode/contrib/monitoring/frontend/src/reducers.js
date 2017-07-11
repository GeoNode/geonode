import { combineReducers } from 'redux';
import theme from './containers/reducers';
import { backend, notifications } from './containers/app/reducers';
import geonodeAverageResponse from './components/cels/geonode-data/reducers';
import { geonodeCpuStatus, geonodeMemStatus } from './components/cels/geonode-status/reducers';
import interval from './components/organisms/header/reducers';


const reducers = {
  backend,
  geonodeAverageResponse,
  geonodeCpuStatus,
  geonodeMemStatus,
  interval,
  notifications,
  theme,
};


const rootReducer = combineReducers(reducers);

export default rootReducer;
