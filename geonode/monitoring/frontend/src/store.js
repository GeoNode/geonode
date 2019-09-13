import { createStore, applyMiddleware } from 'redux';
import { composeWithDevTools } from 'redux-devtools-extension';
import thunk from 'redux-thunk';
import rootReducer from './reducers';

const enhancer = __DEVELOPMENT__
    ? composeWithDevTools(applyMiddleware(thunk))
    : applyMiddleware(thunk);

function configureStore(initialState) {
    if (__DEVELOPMENT__) {
        const store = createStore(rootReducer, initialState, enhancer);
        if (module.hot) {
            module.hot.accept('./reducers', () =>
                store.replaceReducer(require('./reducers').default)
            );
        }
        return store;
    }
    return createStore(rootReducer, initialState, enhancer);
}

const store = configureStore();

export default store;
