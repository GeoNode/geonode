var {createStore, combineReducers, applyMiddleware} = require('redux');

var thunkMiddleware = require('redux-thunk');
var mapConfig = require('../../../reducers/config');

 // reducers
const reducers = combineReducers({
    mapConfig
});

// compose middleware(s) to createStore
let finalCreateStore = applyMiddleware(thunkMiddleware)(createStore);

// export the store with the given reducers (and middleware applied)
module.exports = finalCreateStore(reducers, {});
