/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {Pagination} = require('react-bootstrap');

const RulesTablePagination = React.createClass({
    propTypes: {
        loadRules: React.PropTypes.func,
        rulesPage: React.PropTypes.number,
        rulesCount: React.PropTypes.number
    },
    getDefaultProps() {
        return {
            loadRules: () => {},
            rulesPage: 1,
            rulesCount: 0
        };
    },
    render() {
        const numberOfPages = Math.ceil(this.props.rulesCount / 10);
        return (
            <div className="rules-pagination">
                <Pagination bsSize="small" prev next first last ellipsis boundaryLinks
                    items={numberOfPages}
                    maxButtons={3}
                    activePage={this.props.rulesPage}
                    onSelect={(event, selectEvent) => this.props.loadRules(selectEvent.eventKey, false)}/>
            </div>
        );
    }
});

module.exports = RulesTablePagination;
