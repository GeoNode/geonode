import React from 'react';
import Datamap from 'datamaps';
import styles from './styles';


class WorldMap extends React.Component {
  componentDidMount() {
    const basicChoropleth = new Datamap({
      element: this.d3Element,
      projection: 'mercator',
      fills: {
        defaultFill: '#ABDDA4',
        '0-100': '#fa0fa0',
        '100-200': '#fabda0',
        '200-300': '#3a0fa0',
      },
      data: {
        USA: { fillKey: '0-100' },
        JPN: { fillKey: '100-200' },
        ITA: { fillKey: '200-300' },
        CRI: { fillKey: '0-100' },
        KOR: { fillKey: '100-200' },
        DEU: { fillKey: '200-300' },
      },
    });
    basicChoropleth.legend();
  }

  render() {
    return (
      <div style={styles.root} ref={(node) => {this.d3Element = node;}} />
    );
  }
}


export default WorldMap;
