/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const {Panel, Glyphicon} = require('react-bootstrap');
const Draggable = require('react-draggable');
const {connect} = require('react-redux');
const Localized = require('../../../components/I18N/Localized');
const FeatureGrid = require('../../../components/data/featuregrid/FeatureGrid');
const {changeMapView} = require('../../../actions/map');
const {selectFeatures} = require('../../../actions/featuregrid');
const featuregrid = require('../../../reducers/featuregrid');

const {bindActionCreators} = require('redux');

const SmartFeatureGrid = connect((state) => {
    return {
        map: (state.map && state.map) || (state.config && state.config.map),
        features: state.featuregrid.jsonlayer.features || []
    };
}, dispatch => {
    return bindActionCreators({
            selectFeatures: selectFeatures,
            changeMapView: changeMapView
        }, dispatch);
})(FeatureGrid);

module.exports = connect((state) => {
    return {
        messages: state.locale ? state.locale.messages : null,
        locale: state.locale ? state.locale.current : null,
        localeError: state.locale && state.locale.loadingError ? state.locale.loadingError : undefined,
        map: (state.map && state.map) || (state.config && state.config.map),
        featuregrid
    };
})(React.createClass({
    propTypes: {
        messages: React.PropTypes.object,
        title: React.PropTypes.string,
        locale: React.PropTypes.string,
        localeError: React.PropTypes.string,
        style: React.PropTypes.object
    },
    getInitialState: function() {
        return {
          open: false
        };
    },
    renderHeader() {
        let isActive = this.state.open;
        return (
            <span>
                <span>{this.props.title}</span>
                <button onClick={ ()=> this.setState({ open: !this.state.open })} className="close"><Glyphicon glyph={(isActive) ? "glyphicon glyphicon-collapse-down" : "glyphicon glyphicon-expand"}/></button>
            </span>
        );
    },
    render() {
        return (
            <Localized messages={this.props.messages} locale={this.props.locale} loadingError={this.props.localeError}>
               <Draggable start={{x: 0, y: 0}} handle=".panel-heading, .panel-heading *">
                <Panel collapsible expanded={this.state.open} header={this.renderHeader()} style={this.props.style}>
                    <SmartFeatureGrid {...this.props} style={{height: "300px", width: "100%"}}/>
                </Panel>
                </Draggable>

            </Localized>
        );
    }
}));
