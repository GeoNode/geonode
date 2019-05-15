const React = require('react');

const { SketchPicker } = require('react-color');
require('./colorpicker.css');
const ColorPicker = React.createClass({
  propTypes: {
        value: React.PropTypes.shape({r: React.PropTypes.number, g: React.PropTypes.number, b: React.PropTypes.number, a: React.PropTypes.number}),
        onChangeColor: React.PropTypes.func,
        text: React.PropTypes.string,
        line: React.PropTypes.bool,
        disabled: React.PropTypes.bool
    },
  getInitialState() {
      return {
        displayColorPicker: false
      };
  },
  getDefaultProps() {
      return {
          disabled: false,
          line: false,
          text: "Color",
          value: {
              r: 0,
              g: 0,
              b: 0,
              a: 1
          },
        onChangeColor: () => {}
      };
  },
  getStyle() {
      let color = this.state.color || this.props.value;
      return this.props.line ?
      {
        color: `rgba(${ color.r }, ${ color.g }, ${ color.b }, ${ color.a })`,
        background: `rgba(${ 256 - color.r }, ${ 256 - color.g }, ${ 256 - color.b }, 1)`
      }
      :
      {
        background: `rgba(${ color.r }, ${ color.g }, ${ color.b }, ${ color.a })`,
        color: `rgba(${ 256 - color.r }, ${ 256 - color.g }, ${ 256 - color.b }, 1)`
      };
  },
  render() {
      return (
      <div>
        <div className={this.props.disabled ? "cp-disabled" : "cp-swatch" }style={this.getStyle()} onClick={ () => { if (!this.props.disabled) { this.setState({ displayColorPicker: !this.state.displayColorPicker }); } } }>
        {this.props.text}
        </div>
        { this.state.displayColorPicker ? <div className="cp-popover">
          <div className="cp-cover" onClick={ () => { this.setState({ displayColorPicker: false, color: undefined}); this.props.onChangeColor(this.state.color); }}/>
          <SketchPicker color={ this.state.color || this.props.value} onChange={ (color) => { this.setState({ color: color.rgb }); }} />
        </div> : null }

      </div>
    );
  }
});

module.exports = ColorPicker;
