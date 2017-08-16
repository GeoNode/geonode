import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { Style } from 'radium';
import Home from '../../pages/home';
import SWPerf from '../../pages/software-performance';
import HWPerf from '../../pages/hardware-performance';
import Errors from '../../pages/errors';
import ErrorDetails from '../../pages/error-details';
import Alerts from '../../pages/alerts';
import reset from '../../reset.js';
import fonts from '../../fonts/fonts.js';
import actions from './actions';
import styles from './styles';


const mapStateToProps = (/* state */) => ({});


@connect(mapStateToProps, actions)
class App extends React.Component {
  static propTypes = {
    children: PropTypes.node,
  }

  static childContextTypes = {
    socket: PropTypes.object,
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
