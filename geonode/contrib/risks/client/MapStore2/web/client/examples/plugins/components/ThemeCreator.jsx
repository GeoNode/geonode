/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');

const {Button, Glyphicon, Modal, FormGroup, Checkbox} = require('react-bootstrap');

const Codemirror = require('react-codemirror');


require('codemirror/lib/codemirror.css');

require('codemirror/mode/css/css');

const ThemeCreator = React.createClass({
    propTypes: {
        themeCode: React.PropTypes.string,
        error: React.PropTypes.string,
        onApplyTheme: React.PropTypes.func
    },
    getDefaultProps() {
        return {
            themeCode: '',
            onApplyTheme: () => {}
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
            code: this.props.themeCode
        });
    },
    componentWillReceiveProps(newProps) {
        if (newProps.themeCode !== this.props.themeCode) {
            this.setState({
                code: newProps.themeCode
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
                  Live edit your theme
              </Checkbox>
          </FormGroup>
            <Modal show={this.state.configVisible} bsSize="large" backdrop={false} onHide={() => {
                this.setState({
                  configVisible: false
                });
            }}>
                <Modal.Header className="dialog-error-header-side" closeButton>
                    <Modal.Title>Live edit your own theme</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                  <Codemirror style={{width: '500px'}} key="code-mirror" value={this.state.code} onChange={this.updateCode} options={{
                          mode: {name: "css"},
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
        this.props.onApplyTheme(this.state.code);
    },
    toggleCfg() {
        this.setState({configVisible: !this.state.configVisible});
    }
});

module.exports = ThemeCreator;
