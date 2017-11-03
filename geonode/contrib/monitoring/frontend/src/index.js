import React from 'react';
import { render } from 'react-dom';
import Root from './containers/root';
import injectTapEventPlugin from 'react-tap-event-plugin';

// Needed for onTouchTap
// http://stackoverflow.com/a/34015469/988941
injectTapEventPlugin();


const spinner = document.getElementById('spinner');
spinner.style.display = 'none';

render(
  <Root />,
  document.getElementById('monitoring')
);
