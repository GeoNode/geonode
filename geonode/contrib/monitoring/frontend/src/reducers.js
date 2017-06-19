import { combineReducers } from 'redux';
import theme from './containers/reducers';
import { backend, notifications } from './containers/app/reducers';


const reducers = {
  backend,
  notifications,
  theme,
};


const rootReducer = combineReducers(reducers);

export default rootReducer;
