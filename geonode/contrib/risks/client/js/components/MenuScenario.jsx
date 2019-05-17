/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {Panel} = require('react-bootstrap');

const MenuScenario = React.createClass({
    propTypes: {
        dimensions: React.PropTypes.array,
        dim: React.PropTypes.object,
        setDimIdx: React.PropTypes.func
    },
    getDefaultProps() {
        return {
            dimensions: [],
            dim: {},
            setDimIdx: () => {}
        };
    },
    getScenarios(values, current) {
        return values.map((val, idx) => {
            let active = val === current ? 'active' : '';
            return idx === 0 ? null : (<li key={idx} className={active} onClick={() => { this.props.setDimIdx('dim1Idx', idx); }}><a onClick={(e) => { e.preventDefault(); }} href="#">{val}</a></li>);
        });
    },
    renderScenarioPanelHeader(title, resource, color) {
        return (
            <div className="container-fluid">
                <div className="row">
                    <h4 className="text-center">{title}</h4>
                    <div style={{marginTop: 20}}>{resource.text}</div>
                </div>
                <div className="row text-center" style={{borderBottom: '1px solid ' + color}}>
                    <i className="fa fa-chevron-down" />
                </div>
            </div>
        );
    },
    renderScenarioPanel(title, resource, color) {
        const header = resource ? this.renderScenarioPanelHeader(title, resource, color) : null;
        return resource ? (
            <Panel collapsible header={header} className="panel-box">
                <div className="text-center"style={{fontFamily: 'Georgia, serif', fontStyle: 'italic', marginBottom: 20}}>{resource.title}</div>
                <a target="_blank" href={resource.details}>
                    <div className="row" style={{width: '100%'}}>
                        <div className="col-xs-2"><i className="fa fa-dot-circle-o" /></div>
                        <div className="col-xs-10" dangerouslySetInnerHTML={{__html: resource.abstract}}/>
                    </div>
                </a>
          </Panel>
      ) : (
          <Panel className="panel-box" header={
              <div className="row" style={{borderBottom: '1px solid ' + color, cursor: 'default'}}>
                <h4 className="text-center">{title}</h4>
              </div>}/>
      );
    },
    render() {
        const {dimensions, dim} = this.props;
        const values = dimensions[dim.dim1].values;
        const current = values[dim.dim1Idx];
        const resource = dimensions[dim.dim1].layers[current].resource;
        return (
            <div id="disaster-compare-container">
                {this.renderScenarioPanel('Current: ' + values[0], dimensions[dim.dim1].layers[values[0]].resource, '#ff8f31')}
                <Panel id="disaster-compare-panel" className="panel-box">
                    <h4 className="text-center">{'Risk Reduction Scenario Compared to ' + values[0]}</h4>
                    <ul className="nav nav-pills">
                        {this.getScenarios(values, current)}
                    </ul>
                </Panel>
                {dim.dim1Idx === 0 ? null : this.renderScenarioPanel(dimensions[dim.dim1].name + ' ' + current, resource, '#6646c2')}
            </div>
        );
    }
});

module.exports = MenuScenario;
