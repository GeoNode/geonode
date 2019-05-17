const React = require('react');
const colors = require("./ExtendColorBrewer");

const ColorRampItem = React.createClass({
     propTypes: {
        item: React.PropTypes.object
    },
    render() {
        let ramp = colors[this.props.item.name][5];
        return (<div style={{width: "170px"}}><span style={{marginLeft: "3px"}}>{this.props.item.name}</span>
                    <div style={{width: "20px", height: "20px", backgroundColor: ramp[0], "float": "left"}}/>
                    <div style={{width: "20px", height: "20px", backgroundColor: ramp[1], "float": "left"}}/>
                    <div style={{width: "20px", height: "20px", backgroundColor: ramp[2], "float": "left"}}/>
                    <div style={{width: "20px", height: "20px", backgroundColor: ramp[3], "float": "left"}}/>
                    <div style={{width: "20px", height: "20px", backgroundColor: ramp[4], "float": "left"}}/>
                </div>);
    }
});

module.exports = ColorRampItem;
