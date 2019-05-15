/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {Glyphicon} = require('react-bootstrap');
const Dropzone = require('react-dropzone');
const Spinner = require('react-spinkit');
const Message = require('../../../components/I18N/Message');
  /**
   * A Dropzone area for a thumbnail.
   */

const Thumbnail = React.createClass({
    propTypes: {
        glyphiconRemove: React.PropTypes.string,
        style: React.PropTypes.object,
        loading: React.PropTypes.bool,
        map: React.PropTypes.object,
        // CALLBACKS
        onDrop: React.PropTypes.func,
        onError: React.PropTypes.func,
        onUpdate: React.PropTypes.func,
        onSaveAll: React.PropTypes.func,
        onCreateThumbnail: React.PropTypes.func,
        onDeleteThumbnail: React.PropTypes.func,
        onRemoveThumbnail: React.PropTypes.func,
        // I18N
        message: React.PropTypes.oneOfType([React.PropTypes.string, React.PropTypes.element]),
        suggestion: React.PropTypes.oneOfType([React.PropTypes.string, React.PropTypes.element])
    },
    contextTypes: {
        messages: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            loading: false,
            glyphiconRemove: "remove-circle",
            // CALLBACKS
            onDrop: () => {},
            onError: () => {},
            onUpdate: () => {},
            onSaveAll: () => {},
            onRemoveThumbnail: () => {},
            onCreateThumbnail: () => {},
            onDeleteThumbnail: () => {},
            // I18N
            message: <Message msgId="map.message"/>,
            suggestion: <Message msgId="map.suggestion"/>
        };
    },
    getInitialState() {
        return {};
    },
    onRemoveThumbnail(event) {
        if (event !== null) {
            event.stopPropagation();
        }

        this.files = null;
        this.props.onUpdate(null, null);
        this.props.onRemoveThumbnail();
        this.props.onError([], this.props.map.id);
    },
    getThumbnailUrl() {
        return (this.props.map && this.props.map.newThumbnail && this.props.map.newThumbnail !== "NODATA") ? decodeURIComponent(this.props.map.newThumbnail) : null;
    },
    isImage(images) {
        return images && images[0].type === "image/png" || images && images[0].type === "image/jpeg" || images && images[0].type === "image/jpg";
    },
    getDataUri(images, callback) {
        let filesSelected = images;
        if (filesSelected && filesSelected.length > 0) {
            let fileToLoad = filesSelected[0];
            let fileReader = new FileReader();
            fileReader.onload = (event) => (callback(event.target.result));
            return fileReader.readAsDataURL(fileToLoad);
        }
        return callback(null);
    },
    onDrop(images) {
        // check formats and sizes
        const isAnImage = this.isImage(images);
        let errors = [];

        this.getDataUri(images, (data) => {
            if (isAnImage && data && data.length < 500000) {
                // without errors
                this.props.onError([], this.props.map.id);
                this.files = images;
                this.props.onUpdate(null, images && images[0].preview);
            } else {
                // with at least one error
                if (!isAnImage) {
                    errors.push("FORMAT");
                }
                if (data && data.length >= 500000) {
                    errors.push("SIZE");
                }
                this.props.onError(errors, this.props.map.id);
                this.files = images;
                this.props.onUpdate(null, null);
            }
        });
    },
    generateUUID() {
        // TODO this function should be removed when the unique rule of name of a resource will be dropped
        // and a not unique can be associated to the new thumbnail resources
        let d = new Date().getTime();
        if (window.performance && typeof window.performance.now === "function") {
            d += performance.now(); // use high-precision timer if available
        }
        const uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = (d + Math.random() * 16) % 16 | 0;
            d = Math.floor(d / 16);
            return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
        });
        return uuid;
    },

    updateThumbnail(map, metadata) {
        if (!this.props.map.errors || !this.props.map.errors.length ) {
            this.getDataUri(this.files, (data) => {
                const name = this.generateUUID(); // create new unique name
                const category = "THUMBNAIL";
                // user removed the thumbnail (the original url is present but not the preview)
                if (this.props.map && !data && this.props.map.thumbnail && !this.refs.imgThumbnail && !metadata) {
                    this.deleteThumbnail(this.props.map.thumbnail, this.props.map.id);
                // there is a thumbnail to upload
                }
                if (this.props.map && !data && this.props.map.newThumbnail && !this.refs.imgThumbnail && metadata) {
                    this.deleteThumbnail(this.props.map.thumbnail, this.props.map.id);
                    this.props.onSaveAll(map, metadata, name, data, category, this.props.map.id);
                // there is a thumbnail to upload
                }
                // remove old one if present
                if (this.props.map.newThumbnail && data && this.refs.imgThumbnail) {
                    this.deleteThumbnail(this.props.map.thumbnail, null);
                    // create the new one (and update the thumbnail attribute)
                    this.props.onSaveAll(map, metadata, name, data, category, this.props.map.id);
                }
                // nothing dropped it will be closed the modal
                if (this.props.map.newThumbnail && !data && this.refs.imgThumbnail) {
                    this.props.onSaveAll(map, metadata, name, data, category, this.props.map.id);
                }
                if (!this.props.map.newThumbnail && !data && !this.refs.imgThumbnail) {
                    this.props.onSaveAll(map, metadata, name, data, category, this.props.map.id);
                }
                return data;
            });
        }
    },
    getThumbnailDataUri(callback) {
        this.getDataUri(this.files, callback);
    },
    deleteThumbnail(thumbnail, mapId) {
        if (thumbnail && thumbnail.indexOf("geostore") !== -1) {
            // this doesn't work if the URL is not encoded (because of GeoStore / Tomcat parameter encoding issues)
            let start = (thumbnail).indexOf("data%2F") + 7;
            let end = (thumbnail).indexOf("%2Fraw");
            let idThumbnail = thumbnail.slice(start, end);

            // delete the old thumbnail
            if (idThumbnail) {
                // with mapId != null it will ovveride thumbnail attribute with NODATA value for that map
                this.props.onDeleteThumbnail(idThumbnail, mapId);
            }
        }
    },
    render() {
        const withoutThumbnail = (<div className="dropzone-content-image">{this.props.message}<br/>{this.props.suggestion}</div>);
        return (
            (this.props.loading) ? (<div className="btn btn-info" style={{"float": "center"}}> <Spinner spinnerName="circle" overrideSpinnerClassName="spinner"/></div>) :
            (
                <div className="dropzone-thumbnail-container">
                    <label className="control-label"><Message msgId="map.thumbnail"/></label>
                    <Dropzone multiple={false} className="dropzone alert alert-info" rejectClassName="alert-danger" onDrop={this.onDrop}>
                    { (this.getThumbnailUrl() ) ?
                        (<div>
                            <img src={this.getThumbnailUrl()} ref="imgThumbnail"/>
                            <div className="dropzone-content-image-added">{this.props.message}<br/>{this.props.suggestion}</div>
                            <div className="dropzone-remove" onClick={this.onRemoveThumbnail}>
                                <Glyphicon glyph={this.props.glyphiconRemove} />
                            </div>
                        </div>) : withoutThumbnail
                    }
                    </Dropzone>
                </div>
            )
        );
    }
});

module.exports = Thumbnail;
