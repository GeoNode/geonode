let store;

if (process.env.NODE_ENV === 'production') {
  store = require('./configure-store.prod');
} else {
  store = require('./configure-store.dev');
}


export default store.default;
