/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {findDOMNode} = require('react-dom');
const {Popover, Label, Overlay} = require('react-bootstrap');
const numberLocalizer = require('react-widgets/lib/localizers/simple-number');
numberLocalizer();
const {NumberPicker} = require('react-widgets');
require('./numberpicker.css');

const NumberRenderer = React.createClass({
    propTypes: {
        params: React.PropTypes.object,
        onChangeValue: React.PropTypes.func,
        errorMessage: React.PropTypes.string
    },
    getInitialState() {
        return {
            displayNumberPicker: false,
            showError: false
        };
    },
    getDefaultProps() {
        return {
            onChangeValue: () => {},
            errorMessage: "Value not valid"
        };
    },
    componentDidMount() {
        this.props.params.api.addEventListener('cellClicked', this.cellClicked);
    },
    componentWillUnmount() {
        this.props.params.api.removeEventListener('cellClicked', this.cellClicked);
    },
    getRange() {
        let data = [];
        this.props.params.api.forEachNode((node) => {data.push(node.data); });
        let idx = this.props.params.node.childIndex;
        let min = (data[idx - 1]) ? data[idx - 1].quantity + 0.01 : -Infinity;
        let max = (data[idx + 1]) ? data[idx + 1].quantity - 0.01 : Infinity;
        return {min: min, max: max};
    },
    render() {

        return (
            <div onClick={ () => {
                if (!this.state.displayNumberPicker) {
                    this.setState({displayNumberPicker: !this.state.displayNumberPicker});
                }} }
                >
                { this.state.displayNumberPicker ? (
                    <div>
                        <div style={{position: "fixed", top: 0, right: 0, bottom: 0, left: 0}}
                            onClick={this.stopEditing}/>
                    <div className="numberpicker" onClickCapture={ (e) => {e.stopPropagation(); }}>
                        <NumberPicker ref="colorMapNumberPicker"
                        format="-#,###.##"
                        precision={3}
                        value={this.state.value === undefined ? this.props.params.value : this.state.value}
                        onChange={this.changeNumber}
                        />
                    <Overlay
                        target={() => findDOMNode(this.refs.colorMapNumberPicker)}
                        show={this.state.showError} placement="top" >
                        <Popover id="quantitypickererror" style={{maxWidht: 400}}>
                            <Label bsStyle="danger" >{this.props.errorMessage}</Label>
                        </Popover>
                    </Overlay>
                    </div>
                    </div>) :
                <span>{(this.props.params.value.toFixed) ? this.props.params.value.toFixed(2) : this.props.params.value}</span> }
            </div>
        );
    },
    cellClicked(e) {
        if (this.props.params.value !== e.value && this.state.displayNumberPicker) {
            this.stopEditing();
        }
    },
    stopEditing() {
        let range = this.getRange();
        let newValue = this.state.value === undefined ? this.props.params.value : this.state.value;
        if (range.min < newValue && newValue < range.max) {
            this.setState({ displayNumberPicker: false, showError: false});
            if (newValue !== this.props.params.value) {
                this.props.onChangeValue(this.props.params.node, newValue);
            }
        } else {
            this.setState({showError: true});
        }

    },
    changeNumber(value) {
        this.setState({value: value, showError: false});
    }
});

module.exports = NumberRenderer;
