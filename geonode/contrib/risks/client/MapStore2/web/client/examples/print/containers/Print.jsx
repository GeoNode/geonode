/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const Debug = require('../../../components/development/Debug');
const Localized = require('../../../components/I18N/Localized');
const {connect} = require('react-redux');

const PrintMap = require('../components/PrintMap');
const PrintPreview = require('../components/PrintPreview');

var {changeZoomLevel} = require('../../../actions/map');

const ScaleBox = connect((state) => ({
    currentZoomLvl: (state.map && state.map.zoom) || (state.config && state.config.map && state.config.map.zoom)
}), {
    onChange: changeZoomLevel
})(require("../../../components/mapcontrols/scale/ScaleBox"));

const Print = React.createClass({
    propTypes: {
        messages: React.PropTypes.object,
        locale: React.PropTypes.string,
        enabled: React.PropTypes.bool
    },
    render() {
        return (<Localized messages={this.props.messages} locale={this.props.locale}>
            <div className="fill">
                <PrintMap/>
                {this.props.enabled ? <PrintPreview
                    title="Print Preview" style={{
                            position: "absolute",
                            top: "10px",
                            left: "40px",
                            zIndex: 100}}/> : null}
                    <ScaleBox/>
                <Debug/>
            </div>
        </Localized>);
    }

});
module.exports = connect((state) => {
    return {
        enabled: state.map && state.print.capabilities && true || false,
        locale: state.locale && state.locale.current,
        messages: state.locale && state.locale.messages || {}
    };
})(Print);
