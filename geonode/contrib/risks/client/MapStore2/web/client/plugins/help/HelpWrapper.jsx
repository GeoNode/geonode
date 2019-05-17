/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const {connect} = require('react-redux');

const {changeHelpwinVisibility, changeHelpText} = require('../../actions/help');

module.exports = connect((state) => ({
    helpEnabled: state.controls && state.controls.help && state.controls.help.enabled
}), {
    changeHelpText,
    changeHelpwinVisibility
})(require('../../components/help/HelpWrapper'));
