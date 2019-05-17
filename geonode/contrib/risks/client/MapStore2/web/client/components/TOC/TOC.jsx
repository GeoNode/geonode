/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var React = require('react');
var Sortable = require('react-sortable-items');
require('./css/toc.css');
const TOC = React.createClass({
    propTypes: {
        filter: React.PropTypes.func,
        nodes: React.PropTypes.array,
        id: React.PropTypes.string,
        onSort: React.PropTypes.func
    },
    getDefaultProps() {
        return {
            filter() {return true; },
            nodes: [],
            id: 'mapstore-layers',
            onSort: null
        };
    },

    render() {
        var content = [];
        var filteredNodes = this.props.nodes.filter(this.props.filter);
        if (this.props.children) {
            let i = 0;
            content = filteredNodes.map((node) => React.cloneElement(this.props.children, {
                node: node,
                sortData: i++,
                key: node.name || 'default',
                isDraggable: !!this.props.onSort
            }));
        }
        if (this.props.onSort) {
            return (
                <div id={this.props.id}>
                    <Sortable minDragDistance={5} onSort={this.handleSort}>
                        {content}
                    </Sortable>
                </div>
            );
        }
        return <div id={this.props.id}>{content}</div>;
    },
    handleSort: function(reorder) {
        this.props.onSort('root', reorder);
    }
});

module.exports = TOC;
