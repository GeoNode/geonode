/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
 /**
  * Copyright 2016, GeoSolutions Sas.
  * All rights reserved.
  *
  * This source code is licensed under the BSD-style license found in the
  * LICENSE file in the root directory of this source tree.
  */

const React = require('react');
const {FormControl, FormGroup, ControlLabel} = require('react-bootstrap');

  /**
   * A DropDown menu for user details:
   */
const Metadata = React.createClass({
  propTypes: {
      map: React.PropTypes.object,
      // CALLBACKS
      onChange: React.PropTypes.func,

      // I18N
      nameFieldText: React.PropTypes.node,
      descriptionFieldText: React.PropTypes.node,
      namePlaceholderText: React.PropTypes.string,
      descriptionPlaceholderText: React.PropTypes.string
  },
  getDefaultProps() {
      return {
          // CALLBACKS
          onChange: () => {},

          // I18N
          nameFieldText: "Name",
          descriptionFieldText: "Description",
          namePlaceholderText: "Map Name",
          descriptionPlaceholderText: "Map Description"
      };
  },
  render() {
      return (<form ref="metadataForm" onSubmit={this.handleSubmit}>
          <FormGroup>
              <ControlLabel>{this.props.nameFieldText}</ControlLabel>
              <FormControl ref="mapName"
                  key="mapName"
                  hasFeedback
                  type="text"
                  onChange={this.changeName}
                  placeholder={this.props.namePlaceholderText}
                  defaultValue={this.props.map ? this.props.map.name : ""} />
          </FormGroup>
          <FormGroup>
              <ControlLabel>{this.props.descriptionFieldText}</ControlLabel>
              <FormControl ref="mapDescription"
                  key="mapDescription"
                  hasFeedback
                  type="text"
                  onChange={this.changeDescription}
                  placeholder={this.props.descriptionPlaceholderText}
                  defaultValue={this.props.map ? this.props.map.description : ""} />
          </FormGroup>
      </form>);
  },
  changeName(e) {
      this.props.onChange('name', e.target.value);
  },
  changeDescription(e) {
      this.props.onChange('description', e.target.value);
  }
});

module.exports = Metadata;
