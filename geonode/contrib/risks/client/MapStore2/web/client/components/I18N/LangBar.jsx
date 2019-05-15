
/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var React = require('react');
var {ButtonGroup} = require('react-bootstrap');
var LocaleUtils = require('../../utils/LocaleUtils');
var FlagButton = require('./FlagButton');

var LangBar = React.createClass({
    propTypes: {
        id: React.PropTypes.string,
        locales: React.PropTypes.object,
        currentLocale: React.PropTypes.string,
        onLanguageChange: React.PropTypes.func
    },
    getDefaultProps() {
        return {
            id: "mapstore-langselector",
            locales: LocaleUtils.getSupportedLocales(),
            currentLocale: 'en-US',
            onLanguageChange: function() {}
        };
    },
    render() {
        var code;
        var label;
        var list = [];
        for (let lang in this.props.locales) {
            if (this.props.locales.hasOwnProperty(lang)) {
                code = this.props.locales[lang].code;
                label = this.props.locales[lang].description;
                list.push(
                    <FlagButton
                        key={lang}
                        code={code}
                        label={label}
                        lang={lang}
                        active={code === this.props.currentLocale}
                        onFlagSelected={this.props.onLanguageChange}
                        />);
            }
        }
        return (
                <ButtonGroup id={this.props.id} type="select" bsSize="small">
                    {list}
                </ButtonGroup>
        );
    }
});

module.exports = LangBar;
