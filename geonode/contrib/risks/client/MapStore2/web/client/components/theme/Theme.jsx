/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const withSideEffect = require('react-side-effect');

const reducePropsToState = (props) => {
    const innermostProps = props[props.length - 1];
    if (innermostProps) {
        return {
          theme: innermostProps.theme || 'default',
          themeElement: innermostProps.themeElement || 'theme_stylesheet',
          prefix: innermostProps.prefix || 'ms2',
          prefixContainer: innermostProps.prefixContainer && document.querySelector(innermostProps.prefixContainer) || document.body,
          path: innermostProps.path || 'dist/themes'
        };
    }
    return null;
};

const handleStateChangeOnClient = (themeCfg) => {
    if (themeCfg && themeCfg.theme) {
        let link = document.getElementById(themeCfg.themeElement);

        if (!link) {
            link = document.createElement('link');
            link.setAttribute("rel", "stylesheet");
            link.setAttribute("id", themeCfg.themeElement);
            document.head.insertBefore(link, document.head.firstChild);
        }
        const basePath = link.href && link.href.substring(0, link.href.lastIndexOf("/")) || themeCfg.path;
        link.setAttribute('href', basePath + "/" + themeCfg.theme + ".css");

        const prefixContainer = themeCfg.prefixContainer;
        const prefix = themeCfg.prefix;

        if (!prefixContainer.className || prefixContainer.className.indexOf(prefix) === -1) {
            prefixContainer.className = prefixContainer.className + ' ' + prefix;
        }
    }
};

const Theme = React.createClass({
    propTypes: {
        theme: React.PropTypes.string.isRequired
    },
    getDefaultProps() {
        return {
            theme: 'default'
        };
    },
    render() {
        if (this.props.children) {
            return React.Children.only(this.props.children);
        }
        return null;
    }
});

module.exports = withSideEffect(reducePropsToState, handleStateChangeOnClient)(Theme);
