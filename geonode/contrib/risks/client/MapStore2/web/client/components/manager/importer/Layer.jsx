/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const {Panel, Button} = require('react-bootstrap');
const Message = require("../../I18N/Message");


const Layer = React.createClass({
    propTypes: {
        layer: React.PropTypes.object,
        loading: React.PropTypes.bool,
        edit: React.PropTypes.bool,
        panProps: React.PropTypes.object,
        updateLayer: React.PropTypes.func
    },
    getDefaultProps() {
        return {
            layer: {},
            edit: true,
            loading: false,
            updateLayer: () => {}
        };
    },
    getInitialState() {
        return {};
    },
    onChange(event) {
        let state = {};
        state[event.target.name] = event.target.value || "";
        this.setState(state);
    },
    renderInput(name) {
        let input;
        if (name !== "description") {
            input = (<input
                disabled={!this.props.edit || name === "name"}
                name={name}
                key={name}
                type="text"
                style={{width: "100%"}}
                onChange={this.onChange}
                value={this.state[name] !== undefined ? this.state[name] : this.props.layer[name]}
            />);
        } else {
            input = (<textarea
               disabled={!this.props.edit}
               name={name}
               key={name}
               type="text"
               style={{width: "100%"}}
               onChange={this.onChange}
               value={this.state[name] !== undefined ? this.state[name] : this.props.layer[name]}
               />);
        }
        return [ <dt style={{marginBottom: "10px"}} key={"title-" + name}>{name}</dt>,
         (<dd>
             {input}
        </dd>)];
    },
    render() {
        return (<Panel {...this.props.panProps}>
            <dl className="dl-horizontal">
                {["name", "title", "description"].map(this.renderInput)}
            </dl>
            <div style={{"float": "right"}}>
                <Button bsStyle="primary" disabled={!this.isUpdateEnabled()} onClick={() => {this.props.updateLayer(this.state); }}>
                    <Message msgId="importer.task.update" /></Button>
            </div>
        </Panel>);
    },
    isValid() {
        return this.state.name !== "";
    },
    isModified() {
        return Object.keys(this.state).some((element) => {
            return this.state[element] !== this.props.layer[element];

        });
    },
    isUpdateEnabled() {
        return this.isModified() && this.isValid() && !this.props.loading;
    }
});
module.exports = Layer;
