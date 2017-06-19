import React from 'react';
import { Provider } from 'react-redux';
import Main from './main';
import DevTools from './dev-tools';
import store from '../store';


function Root() {
  return (
    <Provider store={store}>
      <div>
        <Main />
        <DevTools />
      </div>
    </Provider>
  );
}

export default Root;
