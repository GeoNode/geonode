/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');

const {connect} = require('react-redux');
const JSONViewer = require('../../../components/data/identify/viewers/JSONViewer');

const {Panel} = require('react-bootstrap');
const Draggable = require('react-draggable');

const {resetQuery} = require('../actions/query');

const Results = React.createClass({
    propTypes: {
        id: React.PropTypes.string,
        result: React.PropTypes.object,
        onClose: React.PropTypes.func
    },
    getDefaultProps() {
        return {
            id: "query-result-viewer",
            onClose: () => {}
        };
    },
    render() {
        return this.props.result.features.length > 0 ? (<Draggable start={{x: 670, y: 45}} handle=".handle_querypanel, .handle_querypanel *">
                    <div>
                        <Panel id={this.props.id} className="querypanel-container" header={<div className="handle_querypanel">Query Results<span onClick={this.props.onClose} className="close">x</span></div>}>
                            <div style={{maxHeight: "500px", overflow: "auto"}}>
                                <JSONViewer response={this.props.result}/>
                            </div>
                        </Panel>
                    </div>
                </Draggable>) : <span/>;
    }
});

module.exports = connect((state) => ({
    result: state.query.result || {features: []}
}), {
    onClose: resetQuery
})(Results);
