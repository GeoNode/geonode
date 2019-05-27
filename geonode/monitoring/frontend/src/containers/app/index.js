import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { Style } from 'radium';

// Pages
import Alerts from '../../pages/alerts';
import AlertConfig from '../../pages/alert-config';
import AlertsSettings from '../../pages/alerts-settings';
import ErrorDetails from '../../pages/error-details';
import Errors from '../../pages/errors';
import HWPerf from '../../pages/hardware-performance';
import Home from '../../pages/home';
import SWPerf from '../../pages/software-performance';

import reset from '../../reset.js';
import fonts from '../../fonts/fonts.js';
import actions from './actions';
import styles from './styles';


const mapStateToProps = (/* state */) => ({});


@connect(mapStateToProps, actions)
class App extends React.Component {
  static propTypes = {
    children: PropTypes.node,
    get: PropTypes.func.isRequired,
  }

  static childContextTypes = {
    socket: PropTypes.object,
  }

  componentWillMount() {
    this.props.get();
  }

  render() {
    return (
      <div style={styles.root}>
        <Style rules={fonts} />
        <Style rules={reset} />
        {this.props.children}
      </div>
    );
  }
}


export default {
  component: App,
  childRoutes: [
    {
      path: '/',
      indexRoute: { component: Home },
      childRoutes: [
        {
          path: 'errors',
          indexRoute: { component: Errors },
          childRoutes: [
            {
              path: ':errorId',
              component: ErrorDetails,
            },
          ],
        },
        {
          path: 'alerts',
          indexRoute: { component: Alerts },
          childRoutes: [
            {
              path: 'settings',
              component: AlertsSettings,
            },
            {
              path: ':alertId',
              component: AlertConfig,
            },
          ],
        },
        {
          path: 'performance/software',
          indexRoute: { component: SWPerf },
        },
        {
          path: 'performance/hardware',
          indexRoute: { component: HWPerf },
        },
      ],
    },
  ],
};
