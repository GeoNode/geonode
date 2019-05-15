/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const Spinner = require('react-spinkit');
const Message = require('../../I18N/Message');
const {Panel, Table, Button, Glyphicon, OverlayTrigger, Tooltip} = require('react-bootstrap');

const TransformsGrid = React.createClass({
    propTypes: {
        loading: React.PropTypes.bool,
        panProps: React.PropTypes.object,
        type: React.PropTypes.string,
        loadTransform: React.PropTypes.func,
        deleteTransform: React.PropTypes.func,
        transforms: React.PropTypes.array,
        deleteAction: React.PropTypes.object,
        placement: React.PropTypes.string
    },
    contextTypes: {
        messages: React.PropTypes.object
    },
    getDefaultProps() {
        // TODO check translations
        return {
            placement: "bottom",
            deleteAction: <Message msgId="importer.transform.delete" />,
            transforms: [],
            loadTransform: () => {},
            deleteTransform: () => {}
        };
    },
    renderTransform(transform, index) {
        let tooltip = <Tooltip id="transform-delete-action">{this.props.deleteAction}</Tooltip>;
        return (<tr key={index}>
                <td key="id"><a onClick={(e) => {e.preventDefault(); this.props.loadTransform(index); }}>{index}</a></td>
                <td key="type">{transform.type}</td>
                <td key="actions">
                    <OverlayTrigger overlay={tooltip} placement={this.props.placement}>
                        <Button bsSize="xsmall" onClick={(e) => {e.preventDefault(); this.props.deleteTransform(index); }}><Glyphicon glyph="remove"/></Button>
                    </OverlayTrigger>
                </td>
            </tr>);
    },
    render() {
        if (this.props.loading && this.props.transforms.length === 0) {
            return (<Spinner noFadeIn overrideSpinnerClassName="spinner" spinnerName="circle"/>);
        }
        return (
            <Panel {...this.props.panProps} header={<span><Message msgId="importer.task.transforms" /></span>}>
            <Table striped bordered condensed hover>
                <thead>
                  <tr>
                    <th><Message msgId="importer.number"/></th>
                    <th><Message msgId="importer.transforms.type" /></th>
                    <th><Message msgId="importer.transforms.actions" /></th>
                  </tr>
                </thead>
                <tbody>
                    {this.props.transforms.map(this.renderTransform)}
                </tbody>
            </Table>
            </Panel>
        );
    }
});
module.exports = TransformsGrid;
