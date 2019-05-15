/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const {connect} = require('react-redux');

module.exports = connect((state) => ({
    locale: state.locale && state.locale.currentLocale,
    messages: state.locale && state.locale.messages || []
}))(require('../../components/I18N/Message'));
