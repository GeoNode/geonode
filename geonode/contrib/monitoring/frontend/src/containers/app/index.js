import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { Style } from 'radium';
import Template from '../../templates/default';
import Home from '../../pages/home';
import SWPerf from '../../pages/swperf';
import HWPerf from '../../pages/hwperf';
import Errors from '../../pages/errors';
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
      component: Template,
      indexRoute: {
        component: Home,
      },
      childRoutes: [
        {
          path: 'errors',
          indexRoute: {
            component: Errors,
          },
        },
        {
          path: 'performance/software',
          indexRoute: {
            component: SWPerf,
          },
        },
        {
          path: 'performance/hardware',
          indexRoute: {
            component: HWPerf,
          },
        },
      ],
    },
  ],
};
