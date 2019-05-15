/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const Message = require('../../I18N/Message');

const BreadCrumb = React.createClass({
    propTypes: {
        loading: React.PropTypes.bool,
        loadImports: React.PropTypes.func,
        loadImport: React.PropTypes.func,
        loadTask: React.PropTypes.func,
        selectedImport: React.PropTypes.object,
        selectedTask: React.PropTypes.object,
        selectedTransform: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            loadImports: () => {},
            loadImport: () => {},
            loadTask: () => {}
        };
    },

    render() {
        if ( this.props.selectedImport && this.props.selectedTask && this.props.selectedTransform) {
            return (<ol className="breadcrumb">
              <li><a href="#" onClick={(e) => {e.preventDefault(); this.props.loadImports(); }}><Message msgId="importer.imports" /></a></li>
              <li><a href="#" onClick={(e) => {e.preventDefault(); this.props.loadImport(this.props.selectedImport.id); }}>
                  <Message msgId="importer.importN" msgParams={{id: this.props.selectedImport.id}}/>
              </a></li>
              <li><a href="#" onClick={(e) => {e.preventDefault(); this.props.loadTask(this.props.selectedImport.id, this.props.selectedTask.id); }}>
                  Package {this.props.selectedTask.id}
              </a></li>
          <li className="active">Transform {this.props.selectedTransform.id}</li>
            </ol>);
        }
        if ( this.props.selectedImport && this.props.selectedTask) {
            return (
            <ol className="breadcrumb">
              <li><a href="#" onClick={(e) => {e.preventDefault(); this.props.loadImports(); }}><Message msgId="importer.imports" /></a></li>
              <li><a href="#" onClick={(e) => {e.preventDefault(); this.props.loadImport(this.props.selectedImport.id); }}>
                  <Message msgId="importer.importN" msgParams={{id: this.props.selectedImport.id}}/>
              </a></li>
              <li className="active">Package {this.props.selectedTask.id}</li>
            </ol>);
        }
        if (this.props.selectedImport) {
            return (
                <ol className="breadcrumb">
                  <li><a href="#" onClick={(e) => {e.preventDefault(); this.props.loadImports(); }}><Message msgId="importer.imports" /></a></li>
                  <li className="active"><Message msgId="importer.importN" msgParams={{id: this.props.selectedImport.id}}/></li>
                </ol>);
        }
        return (
            <ol className="breadcrumb">
              <li className="active"><Message msgId="importer.imports" /></li>
          </ol>);
    }
});
module.exports = BreadCrumb;
