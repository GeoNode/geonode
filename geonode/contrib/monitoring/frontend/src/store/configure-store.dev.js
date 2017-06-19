/* eslint global-require: 0 */
/* eslint import/no-extraneous-dependencies: 0 */

import { createStore, applyMiddleware, compose } from 'redux';
import thunk from 'redux-thunk';
import rootReducer from '../reducers';
import DevTools from '../containers/dev-tools';


const enhancer = compose(
  applyMiddleware(thunk),
  DevTools.instrument(),
);


export default function configureStore(initialState) {
  const store = createStore(rootReducer, initialState, enhancer);

  if (module.hot) {
    module.hot.accept('../reducers', () =>
      store.replaceReducer(require('../reducers').default)
    );
  }

  return store;
}
