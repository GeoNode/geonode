import { combineReducers } from 'redux';
import { reducers as monitoringReducers } from '../monitoring/src/reducers';
const reducers = { };

export default combineReducers({...monitoringReducers, ...reducers});
