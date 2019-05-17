/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const Message = require('../I18N/Message');
const GridCard = require('../misc/GridCard');
const thumbUrl = require('./style/default.png');
const assign = require('object-assign');

const ConfirmModal = require('./modals/ConfirmModal');
const LocaleUtils = require('../../utils/LocaleUtils');

require("./style/mapcard.css");

const MapCard = React.createClass({
    propTypes: {
        // props
        style: React.PropTypes.object,
        map: React.PropTypes.object,
        mapType: React.PropTypes.string,
        // CALLBACKS
        viewerUrl: React.PropTypes.oneOfType([React.PropTypes.string, React.PropTypes.func]),
        onEdit: React.PropTypes.func,
        onMapDelete: React.PropTypes.func
    },
    contextTypes: {
        messages: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            style: {
                backgroundImage: 'url(' + thumbUrl + ')',
                backgroundSize: "cover",
                backgroundPosition: "center",
                backgroundRepeat: "repeat-x"
            },
            // CALLBACKS
            onMapDelete: ()=> {},
            onEdit: ()=> {}
        };
    },
    onEdit: function(map) {
        this.props.onEdit(map);
    },
    onConfirmDelete() {
        this.props.onMapDelete(this.props.map.id);
        this.close();
    },
    onClick(evt) {
        // Users can select Title and Description without triggering the click
        var selection = window.getSelection();
        if (!selection.toString()) {
            this.stopPropagate(evt);
            this.props.viewerUrl(this.props.map);
        }
    },
    getCardStyle() {
        if (this.props.map.thumbnail) {
            return assign({}, this.props.style, {
                backgroundImage: 'url(' + (this.props.map.thumbnail === null || this.props.map.thumbnail === "NODATA" ? thumbUrl : decodeURIComponent(this.props.map.thumbnail)) + ')'
            });
        }
        return this.props.style;
    },
    render: function() {
        var availableAction = [{
            onClick: (evt) => {this.stopPropagate(evt); this.props.viewerUrl(this.props.map); },
            glyph: "chevron-right",
            tooltip: LocaleUtils.getMessageById(this.context.messages, "manager.openInANewTab")
        }];

        if (this.props.map.canEdit === true) {
            availableAction.push({
                 onClick: (evt) => {this.stopPropagate(evt); this.onEdit(this.props.map); },
                 glyph: "wrench",
                 disabled: this.props.map.updating,
                 loading: this.props.map.updating,
                 tooltip: LocaleUtils.getMessageById(this.context.messages, "manager.editMapMetadata")
         }, {
                 onClick: (evt) => {this.stopPropagate(evt); this.displayDeleteDialog(); },
                 glyph: "remove-circle",
                 disabled: this.props.map.deleting,
                 loading: this.props.map.deleting,
                 tooltip: LocaleUtils.getMessageById(this.context.messages, "manager.deleteMap")
         });
        }
        return (
           <GridCard className="map-thumb" style={this.getCardStyle()} header={this.props.map.title || this.props.map.name}
                actions={availableAction} onClick={this.onClick}
               >
               <div className="map-thumb-description">{this.props.map.description}</div>
               <ConfirmModal ref="deleteMapModal" show={this.state ? this.state.displayDeleteDialog : false} onHide={this.close} onClose={this.close} onConfirm={this.onConfirmDelete} titleText={<Message msgId="manager.deleteMap" />} confirmText={<Message msgId="manager.deleteMap" />} cancelText={<Message msgId="cancel" />} body={<Message msgId="manager.deleteMapMessage" />} />
           </GridCard>
        );
    },
    stopPropagate(event) {
        // prevent click on parent container
        const e = event || window.event || {};
        if (e.stopPropagation) {
            e.stopPropagation();
        } else {
            e.cancelBubble = true;
        }
    },
    close() {
        // TODO Launch an action in order to change the state
        this.setState({
            displayDeleteDialog: false
        });
    },
    displayDeleteDialog() {
        this.setState({
            displayDeleteDialog: true
        });
    }
});

module.exports = MapCard;
