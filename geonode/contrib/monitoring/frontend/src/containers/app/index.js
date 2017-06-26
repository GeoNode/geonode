import React from 'react';
import { connect } from 'react-redux';
import { Style } from 'radium';
import Template from '../../templates/default';
import Home from '../../pages/home';
import SWPerf from '../../pages/swperf';
import HWPerf from '../../pages/hwperf';
import reset from '../../reset.js';
import fonts from '../../fonts/fonts.js';
import actions from './actions';


const mapStateToProps = (/* state */) => ({});


@connect(mapStateToProps, actions)
class App extends React.Component {
  static propTypes = {
    children: React.PropTypes.node,
  }

  static childContextTypes = {
    socket: React.PropTypes.object,
  }

  render() {
    return (
      <div>
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
