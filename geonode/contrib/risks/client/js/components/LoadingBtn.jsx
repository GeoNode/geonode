/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const LoadingBtn = (props) => {
    const {onClick, loading, iconClass, label, btnClass} = props;
    return (<button className={btnClass || "btn btn-default pull-right"} onClick={onClick}><i className={loading && "icon-spinner fa-spin" || iconClass}/>&nbsp;{label}</button>);
};

module.exports = LoadingBtn;
