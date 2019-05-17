/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const {bindActionCreators} = require('redux');
const {connect} = require('react-redux');
const {editUser, changeUserMetadata, saveUser} = require('../../../actions/users');


const mapStateToProps = (state) => {
    const users = state && state.users;
    return {
        modal: true,
        show: users && !!users.currentUser,
        user: users && users.currentUser,
        groups: users && users.groups
    };
};
const mapDispatchToProps = (dispatch) => {
    return bindActionCreators({
        onChange: changeUserMetadata.bind(null),
        onClose: editUser.bind(null, null),
        onSave: saveUser.bind(null)
    }, dispatch);
};

module.exports = connect(mapStateToProps, mapDispatchToProps)(require('../../../components/manager/users/UserDialog'));
