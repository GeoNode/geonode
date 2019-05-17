/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const Dropzone = require('react-dropzone');
const Spinner = require('react-spinkit');

const LocaleUtils = require('../../utils/LocaleUtils');

const SelectShape = React.createClass({
    propTypes: {
        text: React.PropTypes.oneOfType([React.PropTypes.string, React.PropTypes.element]),
        loading: React.PropTypes.bool,
        onShapeChoosen: React.PropTypes.func,
        onShapeError: React.PropTypes.func,
        error: React.PropTypes.oneOfType([React.PropTypes.string, React.PropTypes.element]),
        errorMessage: React.PropTypes.string
    },
    contextTypes: {
        messages: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            text: "Drop or click to import a local Shape",
            onShapeChoosen: () => {},
            onShapeError: () => {},
            errorMessage: "shapefile.error.select"
        };
    },
    render() {
        return (
            (this.props.loading) ? (<div className="btn btn-info" style={{"float": "center"}}> <Spinner spinnerName="circle" overrideSpinnerClassName="spinner"/></div>) :
            (<Dropzone rejectClassName="alert-danger" className="alert alert-info" onDrop={this.checkfile}>
              <div className="dropzone-content" style={{textAlign: "center"}}>{this.props.text}</div>
            </Dropzone>)
            );
    },
    checkfile(files) {
        const allZip = (files.filter((file) => { return file.type !== 'application/zip' && file.type !== 'application/x-zip-compressed'; }).length === 0 );
        if (allZip) {
            if (this.props.error) {
                this.props.onShapeError(null);
            }
            this.props.onShapeChoosen(files);
        }else {
            const error = LocaleUtils.getMessageById(this.context.messages, this.props.errorMessage);
            this.props.onShapeError(error);
        }
    }

});

module.exports = SelectShape;
