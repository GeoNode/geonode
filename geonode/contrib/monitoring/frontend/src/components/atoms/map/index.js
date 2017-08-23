import React from 'react';
import Datamap from 'datamaps';
import styles from './styles';


class WorldMap extends React.Component {
  constructor(props) {
    super(props);

    this.renderMap = () => {
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
          USA: {
            fillKey: '4-5',
            val: 5,
          },
        },
        geographyConfig: {
          popupTemplate: (geography, data) => {
            let popup = '<div class="hoverinfo"><strong>';
            popup += `${geography.properties.name}: ${data.val}`;
            popup += '</strong></div>';
            return popup;
          },
        },
      });
      basicChoropleth.legend();
    };
  }

  componentDidMount() {
    this.renderMap();
  }

  componentDidUpdate() {
    while (this.d3Element.hasChildNodes()) {
      this.d3Element.removeChild(this.d3Element.lastChild);
    }
    this.renderMap();
  }

  render() {
    return (
      <div style={styles.root} ref={(node) => {this.d3Element = node;}} />
    );
  }
}


export default WorldMap;
