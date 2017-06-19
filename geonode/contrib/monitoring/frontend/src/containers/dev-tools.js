/* eslint import/no-extraneous-dependencies: 0 */

import React from 'react';
import { createDevTools } from 'redux-devtools';
import DiffMonitor from 'redux-devtools-diff-monitor';
import DockMonitor from 'redux-devtools-dock-monitor';

export default createDevTools(
  <DockMonitor
    toggleVisibilityKey="ctrl-h"
    changePositionKey="ctrl-q"
    defaultIsVisible={false}
  >
    <DiffMonitor />
  </DockMonitor>
);
