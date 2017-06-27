import { combineReducers } from 'redux';
import theme from './containers/reducers';
import { backend, notifications } from './containers/app/reducers';
import geonodeAverageResponse from './components/cels/geonode-data/reducers';


const reducers = {
  backend,
  notifications,
  theme,
  geonodeAverageResponse,
};


const rootReducer = combineReducers(reducers);

export default rootReducer;
