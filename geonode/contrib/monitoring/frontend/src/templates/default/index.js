import React from 'react';
import { DragDropContext as dndContext } from 'react-dnd';
import HTML5Backend from 'react-dnd-html5-backend';
import styles from './styles';


class Template extends React.Component {
  render() {
    return (
      <div style={styles.content}>
        {this.props.children}
      </div>
    );
  }
}


Template.propTypes = {
  children: React.PropTypes.node,
};


export default dndContext(HTML5Backend)(Template);
