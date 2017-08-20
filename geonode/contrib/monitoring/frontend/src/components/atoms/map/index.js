import React from 'react';
import PropTypes from 'prop-types';
import * as d3 from 'd3';
import * as topojson from 'topojson';
import ReactFauxDOM from 'react-faux-dom';
import styles from './styles';
import cities from './cities.json';
import world from './world.json';


class WorldMap extends React.Component {
  static propTypes = {
    chart: PropTypes.node,
    connectFauxDOM: PropTypes.func,
  }

  static defaultProps = {
    chart: <div>loading</div>,
  }

  renderD3() {
    const width = '100%';
    const height = 500;
    const projection = d3.geoMercator()
      .center([0, 5])
      .scale(200)
      .rotate([-180, 0]);

    const faux = ReactFauxDOM.createElement('div');
    const svg = d3.select(faux).append('svg')
      .attr('width', width)
      .attr('height', height);

    const path = d3.geoPath().projection(projection);

    const g = svg.append('g');

    // load and display the World
    g.selectAll('circle')
      .data(cities)
      .enter()
      .append('a')
        .attr('xlink:href', (d) => `https://www.google.com/search?q=${d.city}`)
      .append('circle')
        .attr('cx', (d) => projection([d.lon, d.lat])[0])
        .attr('cy', (d) => projection([d.lon, d.lat])[1])
        .attr('r', 5)
        .style('fill', 'red');

    g.selectAll('path')
      .data(topojson.feature(world, world.objects.countries).features)
      .enter()
      .append('path')
      .attr('d', path);

    // zoom and pan
    const zoom = d3.zoom()
      .on('zoom', () => {
        let transform = `translate(${d3.event.translate.join(',')})`;
        transform += `scale(${d3.event.scale})`;
        g.attr('transform', transform);
        g.selectAll('circle')
          .attr('d', path.projection(projection));
        g.selectAll('path')
          .attr('d', path.projection(projection));
      });
    svg.call(zoom);
    return faux;
  }

  render() {
    return (
      <div style={styles.root}>
        <div className="renderedD3">
          {this.renderD3().toReact()}
        </div>
      </div>
    );
  }
}


export default WorldMap;
