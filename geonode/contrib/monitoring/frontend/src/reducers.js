import { combineReducers } from 'redux';
import theme from './containers/reducers';
import { backend, notifications } from './containers/app/reducers';
import geonodeAverageResponse from './components/cels/geonode-data/reducers';
import geonodeStatus from './components/cels/geonode-data/reducers';
import interval from './components/organisms/header/reducers';


const reducers = {
  backend,
  geonodeAverageResponse,
  geonodeStatus,
  interval,
  notifications,
  theme,
};


const rootReducer = combineReducers(reducers);

export default rootReducer;
