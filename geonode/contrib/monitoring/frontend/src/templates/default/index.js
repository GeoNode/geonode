import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { DragDropContext } from 'react-dnd';
import HTML5Backend from 'react-dnd-html5-backend';
import Home from '../../pages/home';
import styles from './styles';


const mapStateToProps = (/* state */) => ({
});


class Template extends Component {
  render() {
    return (
      <div>
        <div style={styles.content}>
          <Home />
        </div>
      </div>
    );
  }
}

Template.propTypes = {
  children: PropTypes.node,
  dispatch: PropTypes.func.isRequired,
};

Template.contextTypes = {
  router: PropTypes.object.isRequired,
  muiTheme: PropTypes.object.isRequired,
};

Template.defaultProps = {
};

// eslint-disable-next-line new-cap
const TemplateDND = DragDropContext(HTML5Backend)(Template);
export default connect(mapStateToProps)(TemplateDND);
