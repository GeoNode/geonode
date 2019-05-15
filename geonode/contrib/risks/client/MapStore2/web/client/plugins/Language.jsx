/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const {connect} = require('react-redux');

const {loadLocale} = require('../actions/locale');

const assign = require('object-assign');


const LangBar = connect((state) => ({
    currentLocale: state.locale && state.locale.current
}), {
    onLanguageChange: loadLocale.bind(null, null)
})(require('../components/I18N/LangBar'));

module.exports = {
    LanguagePlugin: assign(LangBar, {
        OmniBar: {
            name: 'language',
            position: 4,
            tool: true,
            priority: 1
        }
    }),
    reducers: {}
};
