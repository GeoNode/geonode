/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');

const {Button, Glyphicon, Modal, Checkbox, FormGroup} = require('react-bootstrap');

const Codemirror = require('react-codemirror');


require('codemirror/lib/codemirror.css');

require('codemirror/mode/javascript/javascript');

const PluginCreator = React.createClass({
    propTypes: {
        pluginCode: React.PropTypes.string,
        error: React.PropTypes.string,
        onApplyCode: React.PropTypes.func
    },
    getDefaultProps() {
        return {
            pluginCode: '',
            onApplyCode: () => {}
        };
    },
    getInitialState() {
        return {
            code: "",
            configVisible: false
        };
    },
    componentWillMount() {
        this.setState({
            code: this.props.pluginCode
        });
    },
    componentWillReceiveProps(newProps) {
        if (newProps.pluginCode !== this.props.pluginCode) {
            this.setState({
                code: newProps.pluginCode
            });
        }
    },
    render() {
        return (<li style={{border: "solid 1px lightgrey", borderRadius: "3px", paddingLeft: "10px", paddingRight: "10px", marginBottom: "3px", marginRight: "10px"}} key="plugin-creator">
        <Button bsSize="small" bsStyle="primary" onClick={this.toggleCfg}><Glyphicon glyph={this.state.configVisible ? "minus" : "plus"}/></Button>
            <FormGroup>
              <Checkbox className="pluginEnable" name="toolscontainer"
                  disabled={true}
                  checked={true}
                  >
                  Live edit your plugin
              </Checkbox>
          </FormGroup>
            <Modal show={this.state.configVisible} bsSize="large" backdrop={false} onHide={() => {
                this.setState({
                  configVisible: false
                });
            }}>
                <Modal.Header className="dialog-error-header-side" closeButton>
                    <Modal.Title>Live edit your own plugin</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                  <Codemirror style={{width: '500px'}} key="code-mirror" value={this.state.code} onChange={this.updateCode} options={{
                          mode: {name: "javascript"},
                          lineNumbers: true
                      }}/>
                  <Button key="apply-cfg" bsStyle="primary" onClick={this.applyCode}>Apply</Button>
                  <div className="error">{this.props.error}</div>
                </Modal.Body>
            </Modal>
        </li>);
    },
    updateCode(newCode) {
        this.setState({
            code: newCode
        });
    },
    applyCode() {
        this.props.onApplyCode(this.state.code);
    },
    toggleCfg() {
        this.setState({configVisible: !this.state.configVisible});
    }
});

module.exports = PluginCreator;
