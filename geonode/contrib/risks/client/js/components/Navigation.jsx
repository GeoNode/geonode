/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');

const Navigation = React.createClass({
    propTypes: {
        items: React.PropTypes.arrayOf(
        React.PropTypes.shape({
            label: React.PropTypes.string.isRequired,
            href: React.PropTypes.string,
            geom: React.PropTypes.string
        })),
        zoom: React.PropTypes.func
    },
    getDefaultProps() {
        return {
            items: [],
            zoom: ()=> {}
        };
    },
    onClick(href, geomHref) {
        this.props.zoom(href, geomHref);
    },
    renderItem() {
        const {items} = this.props;
        const length = items.length;
        return items.map((el, idx) => {
            const disable = length - 1 === idx;
            const classes = `btn btn-default ${disable ? 'disabled' : ''}`;
            return (
            <button key={idx} className={classes} onClick={() => !disable ? this.onClick(`${el.href}`, el.geom) : null}>{el.label}</button>);
        });
    },
    render() {
        return (
            <div id="disaster-navigation" className="btn-group">
                <button className="btn btn-default"><i className="icon-pin"></i></button>
                {this.renderItem()}
            </div>
        );
    }
});

module.exports = Navigation;
