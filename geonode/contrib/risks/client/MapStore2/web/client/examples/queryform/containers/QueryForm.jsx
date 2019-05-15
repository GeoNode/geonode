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

const QueryFormMap = require('../components/QueryFormMap');
const SmartQueryForm = require('../components/SmartQueryForm');
const Results = require('../components/Results');

const {Panel, Glyphicon} = require('react-bootstrap');
const Draggable = require('react-draggable');

require('./queryform.css');

const QueryForm = React.createClass({
    propTypes: {
        messages: React.PropTypes.object,
        locale: React.PropTypes.string
    },
    renderHeader() {
        return (
            <div className="handle_querypanel">
                <span>
                    <span><Glyphicon glyph="glyphicon glyphicon-move"/></span>
                </span>
            </div>
        );
    },
    render() {
        return (
            <Localized messages={this.props.messages} locale={this.props.locale}>
                <div>
                    <QueryFormMap/>
                    <Draggable start={{x: 670, y: 15}} handle=".handle_querypanel, .handle_querypanel *">
                        <div>
                            <Panel className="querypanel-container" header={this.renderHeader()} bsStyle="primary">
                                <SmartQueryForm/>
                            </Panel>
                        </div>
                    </Draggable>
                    <Results/>
                    <Debug/>
                </div>
            </Localized>
        );
    }

});

module.exports = connect((state) => {
    return {
        locale: state.locale && state.locale.current,
        messages: state.locale && state.locale.messages || {}
    };
})(QueryForm);
