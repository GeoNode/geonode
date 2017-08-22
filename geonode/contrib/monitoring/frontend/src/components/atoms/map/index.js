import React from 'react';
import Datamap from 'datamaps';
import styles from './styles';


class WorldMap extends React.Component {
  componentDidMount() {
    const basicChoropleth = new Datamap({
      element: this.d3Element,
      projection: 'mercator',
      fills: {
        defaultFill: '#cccccc',
        '0-1': '#9999cc',
        '1-2': '#8888cc',
        '2-3': '#7777cc',
        '3-4': '#6666cc',
        '4-5': '#5555cc',
        '5-6': '#4444cc',
        '6-7': '#3333cc',
        '7-8': '#2222cc',
        '8-9': '#1111cc',
        '9-10': '#0000cc',
      },
      data: {
        USA: { fillKey: '4-5' },
        JPN: { fillKey: '9-10' },
        ITA: { fillKey: '7-8' },
        CRI: { fillKey: '0-1' },
        KOR: { fillKey: '3-4' },
        DEU: { fillKey: '2-3' },
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
