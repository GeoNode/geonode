/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const {round} = require('lodash');
const {Message, DateFormat} = require('../I18N/I18N');
const Spinner = require('react-spinkit');
const {Glyphicon, ProgressBar, Table, Alert} = require('react-bootstrap');

const Dropzone = require('react-dropzone');

const FileUploader = React.createClass({
    propTypes: {
        dropMessage: React.PropTypes.node,
        dropZoneStyle: React.PropTypes.object,
        dropZoneActiveStyle: React.PropTypes.object,
        beforeUploadMessage: React.PropTypes.node,
        // can be a boolean or an object like this : { progress: 0.99 }
        uploading: React.PropTypes.oneOfType([React.PropTypes.bool, React.PropTypes.object]),
        onBeforeUpload: React.PropTypes.func,
        onUpload: React.PropTypes.func,
        uploadAdditionalParams: React.PropTypes.oneOfType([React.PropTypes.array, React.PropTypes.object]),
        // if exists do not run before upload and start directly the upload after drag
        allowUpload: React.PropTypes.object,
        error: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            beforeUploadMessage: <Message msgId="uploader.beforeUpload" />,
            dropMessage: <Message msgId="uploader.dropfile" />,
            dropZoneStyle: {
                borderStyle: "dashed",
                borderWidth: "3px",
                transition: "all 0.3s ease-in-out"
            },
            dropZoneActiveStyle: {
                backgroundColor: "#eee",
                borderWidth: "5px",
                boxShadow: "0px 0px 25px 14px #d9edf7"

            },
            onBeforeUpload: () => {},
            onUpload: () => {}
        };
    },
    getInitialState() {
        return {};
    },

    componentDidUpdate() {
        if (this.props.allowUpload && this.state && this.state.files) {
            this.uploadFiles(this.state.files);
        }
    },
    renderProgress(uploading) {
        if (uploading && uploading.progress) {
            let percent = round(uploading.progress * 100, 2);
            return <ProgressBar key="progressbar" striped now={percent} label={`${percent}%`}/>;
        }

    },
    renderPreview() {
        return (<Table striped bordered condensed hover>
                    <thead>
                        <tr>
                            <th key="hname"><Message msgId="uploader.filename" /></th>
                            <th key="hsize"><Message msgId="uploader.filesize" /></th>
                            <th key="htype"><Message msgId="uploader.type" /></th>
                            <th key="hlast"><Message msgId="uploader.lastModified" /></th>
                        </tr>
                    </thead>
                    <tbody>
                        {this.state.fileList && this.state.fileList.map((file, index) =>
                        (<tr key={"row_" + index}>
                            <td key="name">{file.name}</td>
                            <td key="size">{this.humanFileSize(file.size)}</td>
                            <td key="type">{file.type}</td>
                            <td key="last"><DateFormat value={file.lastModifiedDate} /></td>
                        </tr>) )
        }</tbody></Table>);
    },
    renderError() {
        if (this.props.error) {
            return (<Alert bsStyle="danger">There was an error during the upload: {this.props.error.statusText}<div>{this.props.error.data}</div></Alert>);
        }
    },
    render() {
        if (this.state && this.state.files) {
            return (<div> <Spinner spinnerName="circle" overrideSpinnerClassName="spinner" />{this.props.beforeUploadMessage}{this.renderPreview()}</div>);
        } else if ( this.props && this.props.uploading && !this.state.files ) {
            return (<div>
                <Spinner spinnerName="circle" overrideSpinnerClassName="spinner"/><Message msgId="uploader.uploadingFiles"/>
                {this.renderProgress(this.props.uploading)}
                {this.renderPreview()}
                </div>);
        }

        return (<div><Dropzone
            key="dropzone"
            rejectClassName="alert-danger"
            className="alert alert-info"
            onDrop={this.uploadFiles}
            style={this.props.dropZoneStyle}
            activeStyle={this.props.dropZoneActiveStyle}>
                <div style={{
                        display: "flex",
                        alignItems: "center",
                        width: "100%",
                        height: "100%",
                        justifyContent: "center"
                }}>
                <span style={{
                    width: "100px",
                    height: "100px",
                    textAlign: "center"
                }}>
                    <Glyphicon glyph="upload" />
                    {this.props.dropMessage}
                </span>
                </div>
        </Dropzone>{this.renderError()}</div>);

    },
    humanFileSize(size) {
        var i = Math.floor( Math.log(size) / Math.log(1024) );
        return ( size / Math.pow(1024, i) ).toFixed(2) * 1 + ' ' + ['B', 'kB', 'MB', 'GB', 'TB'][i];
    },
    uploadFiles(files) {
        if (!files) return;
        if (!this.props.allowUpload) {
            this.setState({files: files, fileList: files});
            this.props.onBeforeUpload(files);
        } else {
            this.setState({files: null, fileList: files});
            this.props.onUpload(files, this.props.uploadAdditionalParams);
        }
    }
});
module.exports = FileUploader;
