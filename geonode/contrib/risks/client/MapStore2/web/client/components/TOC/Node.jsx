/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var React = require('react');
var assign = require('object-assign');
const cx = require('classnames');
const ReactCSSTransitionGroup = require('react-addons-css-transition-group');

var SortableMixin = assign(require('react-sortable-items/SortableItemMixin'), {
    renderWithSortable: function(item) {
        var classNames = cx(assign({
          'SortableItem': true,
          'is-dragging': this.props._isDragging,
          'is-undraggable': !this.props.isDraggable,
          'is-placeholder': this.props._isPlaceholder
      }), item.props.className || {});
        return React.cloneElement(
          this.props._isPlaceholder && this.getPlaceholderContent && Object.prototype.toString.call(this.getPlaceholderContent) === '[object Function]'
            ? this.getPlaceholderContent() : item, {
          className: classNames,
          style: assign({}, item.props.style, this.props.sortableStyle),
          key: this.props.sortableIndex,
          onMouseDown: this.handleSortableItemMouseDown,
          onMouseUp: this.handleSortableItemMouseUp
        });
    }
});

var Node = React.createClass({
    propTypes: {
        node: React.PropTypes.object,
        style: React.PropTypes.object,
        styler: React.PropTypes.func,
        className: React.PropTypes.string,
        type: React.PropTypes.string,
        onSort: React.PropTypes.func,
        isDraggable: React.PropTypes.bool,
        animateCollapse: React.PropTypes.bool
    },
    mixins: [SortableMixin],
    getDefaultProps() {
        return {
            node: null,
            style: {},
            styler: () => {},
            className: "",
            type: 'node',
            onSort: null,
            animateCollapse: true
        };
    },
    renderChildren(filter = () => true) {
        return React.Children.map(this.props.children, (child) => {
            if (filter(child)) {
                let props = (child.type.inheritedPropTypes || ['node']).reduce((previous, propName) => {
                    return this.props[propName] ? assign(previous, {[propName]: this.props[propName]}) : previous;
                }, {});
                return React.cloneElement(child, props);
            }
        });
    },
    render() {
        let expanded = (this.props.node.expanded !== undefined) ? this.props.node.expanded : true;
        let prefix = this.props.type;
        const nodeStyle = assign({}, this.props.style, this.props.styler(this.props.node));
        let collapsible = expanded ? this.renderChildren((child) => child && child.props.position === 'collapsible') : [];
        if (this.props.animateCollapse) {
            collapsible = <ReactCSSTransitionGroup transitionName="TOC-Node" transitionEnterTimeout={250} transitionLeaveTimeout={250}>{collapsible}</ReactCSSTransitionGroup>;
        }
        let content = (<div key={this.props.node.name} className={(expanded ? prefix + "-expanded" : prefix + "-collapsed") + " " + this.props.className} style={nodeStyle} >
            {this.renderChildren((child) => child && child.props.position !== 'collapsible')}
            {collapsible}
        </div>);
        return this.props.isDraggable ? this.renderWithSortable(content) : content;
    }
});

module.exports = Node;
